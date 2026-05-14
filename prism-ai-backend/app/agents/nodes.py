from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from langgraph.types import interrupt

from app.core.config import Settings
from app.schemas.common import ConfidenceLevel, RiskLevel, TraceStatus, WorkflowStatus
from app.services.extraction_service import detect_copy_paste_signals, extract_internship_details, normalize_text
from app.services.llm_service import LLMOutcome
from app.services.recommendation_service import build_recommendation
from app.services.rule_engine import RuleEngineResult, evaluate_rules
from app.services.scoring_service import calculate_trust_score, determine_confidence, determine_risk_level, scam_likelihood_from_score
from app.services.trace_service import build_trace, trace_step
from app.services.url_fetch_service import fetch_and_extract_url_text
from app.services.verification_service import verify_company

from app.agents.state import PrismAgentState


@dataclass(slots=True)
class AgentRuntime:
    settings: Settings
    search_service: Any
    llm_service: Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trace(state: PrismAgentState, step: str, label: str, status: TraceStatus | str, detail: str | None = None) -> list[dict[str, Any]]:
    trace = list(state.get("agent_trace") or [])
    trace.append(trace_step(step=step, label=label, status=status, detail=detail, timestamp=_now()))
    return trace


def _review_payload(state: PrismAgentState) -> dict[str, Any]:
    return {
        "type": "human_review_required",
        "scan_id": state.get("scan_id"),
        "message": "Prism AI paused this scan because it needs human review.",
        "trust_score": int(state.get("trust_score") or 0),
        "risk_level": state.get("risk_level") or RiskLevel.needs_manual_verification.value,
        "confidence": state.get("confidence") or ConfidenceLevel.low.value,
        "review_reasons": state.get("human_review_reason") or [],
        "green_flags": state.get("green_flags") or [],
        "red_flags": state.get("red_flags") or [],
        "missing_information": state.get("missing_information") or [],
        "options": ["run_deeper_scan", "generate_safe_message", "mark_suspicious", "continue_anyway", "reject_opportunity"],
    }


def _review_reasons(state: PrismAgentState) -> list[str]:
    extracted = state.get("extracted_details") or {}
    signals = state.get("verification_signals") or {}
    llm = state.get("llm_analysis") or {}
    reasons: list[str] = []
    red_flags = state.get("red_flags") or []

    if (state.get("trust_score") or 0) < 75:
        reasons.append("Trust score is below the human-review threshold.")
    if (state.get("confidence") or "").lower() == ConfidenceLevel.low.value.lower():
        reasons.append("Confidence is low.")
    if state.get("risk_level") in {RiskLevel.high_caution.value, RiskLevel.high_risk.value}:
        reasons.append(f"Risk level is {state.get('risk_level')}.")
    fee_risk = state.get("fee_payment_risk_signals") or {}
    if fee_risk.get("application_fee_mentioned") or fee_risk.get("payment_language_detected"):
        reasons.append("Payment, registration fee, or training fee language was detected.")
    contact_risk = state.get("recruiter_contact_risk_signals") or {}
    if contact_risk.get("private_channel_only"):
        reasons.append("WhatsApp-only or Telegram-only application path detected.")
    if not extracted.get("company"):
        reasons.append("Company name is missing.")
    if signals.get("company_website_found") is False:
        reasons.append("Official company website was not found.")
    if contact_risk.get("gmail_only_risk"):
        reasons.append("Recruiter email appears to be personal Gmail, Yahoo, or Outlook only.")
    if any("sensitive" in flag.get("label", "").lower() or "document" in flag.get("label", "").lower() for flag in red_flags):
        reasons.append("Sensitive personal documents may be requested too early.")
    if any("document" in flag.get("evidence", "").lower() for flag in red_flags):
        reasons.append("Sensitive personal documents may be requested too early.")
    if llm.get("status") == "completed":
        llm_score = llm.get("confidence") or "Low"
        if llm_score == "High" and (state.get("trust_score") or 0) < 60:
            reasons.append("LLM and rule engine appear to disagree strongly.")
    if signals.get("company_footprint") == "weak" and (extracted.get("stipend") or extracted.get("application_channel")):
        reasons.append("Web verification is weak even though the opportunity claims meaningful benefits.")
    if not reasons:
        reasons.append("The opportunity remains uncertain and should be reviewed manually.")
    return list(dict.fromkeys(reasons))


def _normalize_llm_outcome(result: Any) -> dict[str, Any]:
    if result is None:
        return {"status": "skipped"}
    if isinstance(result, LLMOutcome):
        return {"status": result.status, "result": result.result.model_dump() if result.result else None, "raw_output": result.raw_output, "notes": result.notes or []}
    if isinstance(result, dict):
        return result
    return {"status": getattr(result, "status", "failed"), "result": None, "notes": [str(result)]}


def receive_input(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    scan_id = state.get("scan_id") or ""
    input_text = normalize_text(state.get("input_text") or "")
    input_url = state.get("input_url")
    combined_text = normalize_text("\n".join(part for part in [input_text, ""] if part))
    return {
        "scan_id": scan_id,
        "input_text": input_text,
        "input_url": input_url,
        "category": state.get("category") or "internship",
        "combined_text": combined_text,
        "workflow_status": WorkflowStatus.running.value,
        "review_count": int(state.get("review_count") or 0),
        "deeper_scan_attempts": int(state.get("deeper_scan_attempts") or 0),
        "agent_trace": _trace(state, "receive_input", "Received input", TraceStatus.completed, "Request accepted and workflow started."),
    }


def fetch_url_content(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    fetched_text = None
    trace_status = TraceStatus.skipped
    detail = "URL fetch not requested."
    if state.get("input_url") and runtime.settings.enable_url_fetch:
        fetched_text, fetch_meta = fetch_and_extract_url_text(state["input_url"], runtime.settings)
        trace_status = TraceStatus.completed if fetch_meta["status"] == "completed" else TraceStatus.warning if fetch_meta["status"] == "failed" else TraceStatus.skipped
        detail = fetch_meta["detail"]
    elif state.get("input_url"):
        detail = "URL fetching is disabled by configuration."
    combined_text = normalize_text("\n".join(part for part in [state.get("input_text") or "", fetched_text or ""] if part))
    updates: PrismAgentState = {
        "fetched_text": fetched_text,
        "combined_text": combined_text,
        "agent_trace": _trace(state, "fetch_url_content", "Fetched URL content", trace_status, detail),
    }
    return updates


def extract_details(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    extracted = extract_internship_details(state.get("combined_text") or "")
    copy_paste = detect_copy_paste_signals(state.get("combined_text") or "")
    return {
        "extracted_details": extracted,
        "duplicate_copy_paste_signals": copy_paste,
        "agent_trace": _trace(state, "extract_details", "Extracted opportunity details", TraceStatus.completed, "Structured details were derived from the input text."),
    }


def run_rule_checks(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    rules = evaluate_rules(state.get("combined_text") or "", state.get("extracted_details") or {}, state.get("verification_signals"))
    return {
        "green_flags": rules.green_flags,
        "red_flags": rules.red_flags,
        "missing_information": rules.missing_information,
        "fee_payment_risk_signals": rules.fee_payment_risk_signals,
        "unrealistic_claim_signals": rules.unrealistic_claim_signals,
        "recruiter_contact_risk_signals": rules.recruiter_contact_risk_signals,
        "agent_trace": _trace(state, "run_rule_checks", "Checked scam-risk rules", TraceStatus.completed, "Rule-based scam signals were evaluated."),
    }


def run_web_verification(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    company = (state.get("extracted_details") or {}).get("company")
    source_results = None
    verification_signals = {
        "company_website_found": None,
        "official_domain_match": None,
        "company_footprint": "unknown",
        "duplicate_post_risk": (state.get("duplicate_copy_paste_signals") or {}).get("duplicate_post_risk", "unknown"),
        "search_results_checked": 0,
        "suspicious_source_notes": [],
    }
    sources: list[dict[str, Any]] = []
    trace_status = TraceStatus.skipped
    detail = "Company verification skipped."
    if company and runtime.settings.enable_web_search:
        search_outcome = runtime.search_service.search_company(company, (state.get("extracted_details") or {}).get("title"), deep_scan=bool(state.get("deeper_scan_attempts")))
        source_results = {"status": search_outcome.status, "results": search_outcome.results, "notes": search_outcome.notes}
        verification, sources_model = verify_company(company, source_results)
        verification_signals = verification.model_dump()
        sources = [source.model_dump() for source in sources_model]
        trace_status = TraceStatus.completed if search_outcome.status == "completed" else TraceStatus.warning if search_outcome.status == "failed" else TraceStatus.skipped
        detail = f"{verification_signals.get('search_results_checked', 0)} sources checked."
    elif company:
        detail = "Web search is disabled or unavailable."
    return {
        "source_results": source_results,
        "verification_signals": verification_signals,
        "company_verification_sources": sources,
        "agent_trace": _trace(state, "run_web_verification", "Verified company signals", trace_status, detail),
    }


def run_llm_analysis(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    try:
        outcome = runtime.llm_service.analyze(state.get("combined_text") or "", state.get("extracted_details") or {}, state.get("source_results"))
    except Exception as exc:  # pragma: no cover - defensive
        outcome = {"status": "failed", "notes": [str(exc)]}
    normalized = _normalize_llm_outcome(outcome)
    trace_status = TraceStatus.completed if normalized.get("status") == "completed" else TraceStatus.warning if normalized.get("status") == "failed" else TraceStatus.skipped
    detail = "Structured reasoning was returned by the LLM provider." if normalized.get("status") == "completed" else "LLM failed; Prism continued with rule-based analysis." if normalized.get("status") == "failed" else "LLM analysis was skipped or unavailable."
    return {
        "llm_analysis": normalized,
        "agent_trace": _trace(state, "run_llm_analysis", "Ran LLM analysis", trace_status, detail),
    }


def calculate_score(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    llm_analysis = state.get("llm_analysis") or {}
    extracted = state.get("extracted_details") or {}
    verification = state.get("verification_signals") or {}
    rules = type("Rules", (), {
        "fee_payment_risk_signals": state.get("fee_payment_risk_signals") or {},
        "red_flags": state.get("red_flags") or [],
    })()
    trust_score = calculate_trust_score(extracted, rules, verification, llm_analysis)
    scam_likelihood = scam_likelihood_from_score(trust_score)
    confidence = determine_confidence(extracted, verification, llm_analysis.get("status") == "completed", len(state.get("combined_text") or ""))
    risk_level = determine_risk_level(trust_score, "low" if confidence == ConfidenceLevel.low else "medium")
    return {
        "trust_score": trust_score,
        "scam_likelihood": scam_likelihood,
        "confidence": confidence.value if hasattr(confidence, "value") else str(confidence),
        "risk_level": risk_level,
        "agent_trace": _trace(state, "calculate_score", "Calculated trust score", TraceStatus.completed, f"Trust score set to {trust_score}/100."),
    }


def risk_gate(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    reasons = _review_reasons(state)
    requires = any(
        [
            (state.get("trust_score") or 0) < 75,
            (state.get("confidence") or "").lower() == ConfidenceLevel.low.value.lower(),
            state.get("risk_level") in {RiskLevel.high_caution.value, RiskLevel.high_risk.value},
            bool((state.get("fee_payment_risk_signals") or {}).get("application_fee_mentioned")),
            bool((state.get("fee_payment_risk_signals") or {}).get("payment_language_detected")),
            bool((state.get("recruiter_contact_risk_signals") or {}).get("private_channel_only")),
            not (state.get("extracted_details") or {}).get("company"),
            (state.get("verification_signals") or {}).get("company_website_found") is False,
            bool((state.get("recruiter_contact_risk_signals") or {}).get("gmail_only_risk")),
            bool((state.get("red_flags") or [])),
            ((state.get("verification_signals") or {}).get("company_footprint") == "weak" and bool((state.get("extracted_details") or {}).get("stipend"))),
            bool((state.get("unrealistic_claim_signals") or {}).get("unrealistic_claim_detected")),
        ]
    )
    review_count = int(state.get("review_count") or 0)
    if requires and review_count < 2:
        payload = _review_payload({**state, "human_review_reason": reasons})
        return {
            "requires_human_review": True,
            "human_review_reason": reasons,
            "human_review_payload": payload,
            "workflow_status": WorkflowStatus.awaiting_human_review.value,
            "review_count": review_count + 1,
            "agent_trace": _trace(state, "risk_gate", "Paused for human review", TraceStatus.awaiting_review, "; ".join(reasons)),
        }
    return {
        "requires_human_review": False,
        "human_review_reason": reasons,
        "human_review_payload": None,
        "workflow_status": WorkflowStatus.running.value,
        "agent_trace": _trace(state, "risk_gate", "Passed risk gate", TraceStatus.completed, "Workflow can continue without human review."),
    }


def human_review(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    review_payload = state.get("human_review_payload") or _review_payload(state)
    resume_value = interrupt(review_payload)
    if isinstance(resume_value, dict):
        decision = str(resume_value.get("decision") or "").strip()
        notes = resume_value.get("notes")
    else:
        decision = str(resume_value or "").strip()
        notes = None
    return {
        "human_decision": decision,
        "human_notes": notes,
        "requires_human_review": False,
        "workflow_status": WorkflowStatus.running.value,
        "agent_trace": _trace(state, "human_review", "Human review completed", TraceStatus.completed, f"Decision received: {decision or 'none'}."),
    }


def deeper_scan(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    attempts = int(state.get("deeper_scan_attempts") or 0)
    if attempts >= 2:
        return {
            "agent_trace": _trace(state, "deeper_scan", "Skipped deeper scan", TraceStatus.skipped, "Maximum deeper-scan attempts reached."),
        }
    company = (state.get("extracted_details") or {}).get("company")
    if not company:
        return {
            "deeper_scan_attempts": attempts + 1,
            "agent_trace": _trace(state, "deeper_scan", "Ran deeper scan", TraceStatus.warning, "Company name was unavailable, so deeper verification was limited."),
        }
    search_outcome = runtime.search_service.search_company(company, (state.get("extracted_details") or {}).get("title"), deep_scan=True)
    verification, sources_model = verify_company(company, {"results": search_outcome.results, "status": search_outcome.status, "notes": search_outcome.notes})
    verification_signals = verification.model_dump()
    merged_sources = list(state.get("company_verification_sources") or []) + [source.model_dump() for source in sources_model]
    updated_reasons = _review_reasons({**state, "verification_signals": verification_signals, "company_verification_sources": merged_sources, "deeper_scan_attempts": attempts + 1})
    return {
        "source_results": {"status": search_outcome.status, "results": search_outcome.results, "notes": search_outcome.notes},
        "verification_signals": verification_signals,
        "company_verification_sources": merged_sources,
        "human_review_reason": updated_reasons,
        "deeper_scan_attempts": attempts + 1,
        "agent_trace": _trace(state, "deeper_scan", "Ran deeper verification", TraceStatus.completed if search_outcome.status == "completed" else TraceStatus.warning, "Deep search queries were executed and verification signals were refreshed."),
    }


def generate_recommendation(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    extracted = state.get("extracted_details") or {}
    trust_score = int(state.get("trust_score") or 0)
    risk_level = state.get("risk_level") or RiskLevel.needs_manual_verification.value
    human_decision = (state.get("human_decision") or "").strip()
    green_flags = state.get("green_flags") or []
    red_flags = state.get("red_flags") or []
    recommended_action, safe_message, summary = build_recommendation(extracted, trust_score, risk_level, green_flags, red_flags, state.get("verification_signals"))

    if human_decision == "generate_safe_message":
        safe_message = f"Hi, I’m interested in the {extracted.get('title') or 'role'} at {extracted.get('company') or 'your company'}. Could you please confirm the official application process, stipend, duration, responsibilities, whether any fee is required, and the official email or website?"
        recommended_action = "Review the message manually before sending. Do not send it automatically."
    elif human_decision == "mark_suspicious":
        risk_level = RiskLevel.high_risk.value if risk_level != RiskLevel.high_risk.value else risk_level
        recommended_action = "Avoid or verify manually before proceeding."
    elif human_decision == "continue_anyway":
        recommended_action = "Proceed only if you verify through official company channels. Do not pay any fee or share sensitive documents early."
        if trust_score < 70:
            summary = f"Caution remains high. {summary}"
    elif human_decision == "reject_opportunity":
        risk_level = RiskLevel.high_risk.value
        recommended_action = "Do not proceed with this opportunity."
        summary = "The opportunity was rejected after human review."

    return {
        "recommended_action": recommended_action,
        "safe_message": safe_message,
        "risk_level": risk_level,
        "workflow_status": WorkflowStatus.rejected.value if human_decision == "reject_opportunity" else WorkflowStatus.completed.value,
        "final_result": {
            "trust_score": trust_score,
            "risk_level": risk_level,
            "summary": summary,
            "human_decision": human_decision or None,
        },
        "agent_trace": _trace(state, "generate_recommendation", "Generated recommendation", TraceStatus.completed, "Final action guidance and safe message were prepared."),
    }


def save_result(state: PrismAgentState, runtime: AgentRuntime) -> PrismAgentState:
    final_result = {
        "scan_id": state.get("scan_id"),
        "workflow_status": state.get("workflow_status") or WorkflowStatus.completed.value,
        "requires_human_review": bool(state.get("requires_human_review")),
        "human_review_reason": state.get("human_review_reason") or [],
        "human_decision": state.get("human_decision"),
        "trust_score": state.get("trust_score") or 0,
        "scam_likelihood": state.get("scam_likelihood") or 0,
        "risk_level": state.get("risk_level") or RiskLevel.needs_manual_verification.value,
        "confidence": state.get("confidence") or ConfidenceLevel.low.value,
        "summary": (state.get("final_result") or {}).get("summary") or "",
    }
    return {
        "final_result": final_result,
        "graph_checkpoint_id": state.get("graph_checkpoint_id") or f"{state.get('scan_id')}:final",
        "agent_trace": _trace(state, "save_result", "Saved result", TraceStatus.completed, "The final workflow state was persisted."),
    }
