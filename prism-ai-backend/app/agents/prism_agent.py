from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from langgraph.types import Command
from sqlalchemy.orm import Session

from app.agents.graph import build_graph
from app.agents.nodes import AgentRuntime
from app.agents.state import PrismAgentState
from app.core.config import Settings, get_settings
from app.models.scan import Scan
from app.repositories.scan_repository import ScanRepository
from app.schemas.common import ConfidenceLevel, FlagItem, HumanReviewPayload, HumanReviewResponse, RiskLevel, WorkflowStatus
from app.schemas.scan import ReviewDecisionRequest, ScanCreateRequest, ScanCreateResponse
from app.services.llm_service import LLMService
from app.services.recommendation_service import build_recommendation
from app.services.search_service import SearchService


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_trace_payload(state: PrismAgentState) -> list[dict]:
    return list(state.get("agent_trace") or [])


def _build_human_review(state: PrismAgentState) -> HumanReviewPayload:
    return HumanReviewPayload(
        scan_id=str(state.get("scan_id")),
        message="Prism AI paused this scan because it needs human review.",
        trust_score=int(state.get("trust_score") or 0),
        risk_level=state.get("risk_level") or RiskLevel.needs_manual_verification.value,
        confidence=state.get("confidence") or ConfidenceLevel.low.value,
        review_reasons=state.get("human_review_reason") or [],
        green_flags=[FlagItem.model_validate(item) for item in state.get("green_flags") or []],
        red_flags=[FlagItem.model_validate(item) for item in state.get("red_flags") or []],
        missing_information=state.get("missing_information") or [],
    )


def _response_from_state(state: PrismAgentState, scan: Scan | None = None) -> ScanCreateResponse:
    human_review = _build_human_review(state) if state.get("requires_human_review") or state.get("workflow_status") == WorkflowStatus.awaiting_human_review.value else None
    extracted = state.get("extracted_details") or {}
    final_result = state.get("final_result") or {}
    return ScanCreateResponse(
        scan_id=UUID(str(state.get("scan_id"))) if state.get("scan_id") else (scan.id if scan else uuid4()),
        category=state.get("category") or "internship",
        workflow_status=state.get("workflow_status") or WorkflowStatus.completed.value,
        requires_human_review=bool(state.get("requires_human_review")),
        human_review=human_review,
        human_review_reason=state.get("human_review_reason") or [],
        human_decision=state.get("human_decision"),
        human_notes=state.get("human_notes"),
        graph_thread_id=state.get("graph_thread_id") or (str(scan.id) if scan else None),
        checkpoint_id=state.get("graph_checkpoint_id"),
        analysis_available=True,
        risk_level=state.get("risk_level") or RiskLevel.needs_manual_verification.value,
        trust_score=state.get("trust_score"),
        scam_likelihood=state.get("scam_likelihood"),
        confidence=state.get("confidence") or ConfidenceLevel.low.value,
        summary=final_result.get("summary") or state.get("summary") or "",
        extracted_details=extracted,
        green_flags=[FlagItem.model_validate(item) for item in state.get("green_flags") or []],
        red_flags=[FlagItem.model_validate(item) for item in state.get("red_flags") or []],
        missing_information=state.get("missing_information") or [],
        verification_signals=state.get("verification_signals") or {},
        duplicate_copy_paste_signals=state.get("duplicate_copy_paste_signals") or {},
        fee_payment_risk_signals=state.get("fee_payment_risk_signals") or {},
        unrealistic_claim_signals=state.get("unrealistic_claim_signals") or {},
        recruiter_contact_risk_signals=state.get("recruiter_contact_risk_signals") or {},
        recommended_action=state.get("recommended_action") or "",
        safe_message=state.get("safe_message") or "",
        agent_trace=_extract_trace_payload(state),
        company_verification_sources=state.get("company_verification_sources") or [],
        raw_llm_output=state.get("llm_analysis") or None,
        source_results=state.get("source_results") or None,
        final_result=final_result or None,
    )


def _state_from_scan(scan: Scan) -> PrismAgentState:
    return {
        "scan_id": str(scan.id),
        "input_text": scan.input_text or "",
        "input_url": scan.input_url,
        "category": scan.category,
        "fetched_text": scan.fetched_text,
        "combined_text": "\n".join(part for part in [scan.input_text or "", scan.fetched_text or ""] if part),
        "extracted_details": {
            "title": scan.extracted_title,
            "company": scan.extracted_company,
            "mode": scan.extracted_mode,
            "stipend": scan.extracted_stipend,
            "duration": scan.extracted_duration,
            "skills": scan.extracted_skills or [],
        },
        "green_flags": scan.green_flags or [],
        "red_flags": scan.red_flags or [],
        "missing_information": scan.missing_information or [],
        "verification_signals": scan.verification_signals or {},
        "llm_analysis": scan.raw_llm_output or {},
        "trust_score": scan.trust_score,
        "scam_likelihood": scan.scam_likelihood,
        "risk_level": scan.risk_level,
        "confidence": scan.confidence,
        "requires_human_review": scan.requires_human_review,
        "human_review_reason": scan.human_review_reason or [],
        "human_review_payload": None,
        "human_decision": scan.human_decision,
        "human_notes": scan.human_notes,
        "recommended_action": scan.recommended_action or "",
        "safe_message": scan.safe_message or "",
        "agent_trace": scan.agent_trace or [],
        "final_result": scan.final_result or {},
        "company_verification_sources": scan.source_results.get("results", []) if isinstance(scan.source_results, dict) else [],
        "source_results": scan.source_results,
        "duplicate_copy_paste_signals": {},
        "fee_payment_risk_signals": {},
        "unrealistic_claim_signals": {},
        "recruiter_contact_risk_signals": {},
        "workflow_status": scan.workflow_status,
        "review_count": 1 if scan.requires_human_review else 0,
        "deeper_scan_attempts": 0,
        "graph_thread_id": scan.graph_thread_id or str(scan.id),
        "graph_checkpoint_id": scan.checkpoint_id,
    }


def _snapshot_scan_response(scan: Scan) -> ScanCreateResponse:
    return _response_from_state(_state_from_scan(scan), scan)


@dataclass
class PrismAgent:
    settings: Settings

    def __post_init__(self) -> None:
        self.repository = ScanRepository()
        self.search_service = SearchService(self.settings)
        self.llm_service = LLMService(self.settings)
        self.runtime = AgentRuntime(settings=self.settings, search_service=self.search_service, llm_service=self.llm_service)
        self.graph = build_graph(self.runtime)

    def _seed_scan(self, db: Session, request: ScanCreateRequest, scan_id: UUID | None = None) -> Scan:
        scan = Scan(id=scan_id or uuid4(), category=request.category)
        scan.input_text = request.text
        scan.input_url = request.url
        scan.workflow_status = WorkflowStatus.running.value
        scan.requires_human_review = False
        scan.human_review_reason = []
        scan.human_decision = None
        scan.human_notes = None
        scan.graph_thread_id = str(scan.id)
        scan.checkpoint_id = None
        scan.agent_trace = []
        self.repository.create(db, scan)
        return scan

    def _state_to_scan(self, db: Session, scan: Scan, state: PrismAgentState) -> Scan:
        scan.input_text = state.get("input_text")
        scan.input_url = state.get("input_url")
        scan.fetched_text = state.get("fetched_text")
        scan.workflow_status = state.get("workflow_status") or WorkflowStatus.completed.value
        scan.requires_human_review = bool(state.get("requires_human_review"))
        scan.human_review_reason = state.get("human_review_reason") or []
        scan.human_decision = state.get("human_decision")
        scan.human_notes = state.get("human_notes")
        scan.graph_thread_id = state.get("graph_thread_id") or str(scan.id)
        scan.checkpoint_id = state.get("graph_checkpoint_id")
        scan.review_requested_at = scan.review_requested_at or (datetime.now(timezone.utc) if scan.requires_human_review else None)
        scan.review_completed_at = datetime.now(timezone.utc) if scan.human_decision else scan.review_completed_at
        scan.category = state.get("category") or scan.category
        scan.extracted_title = (state.get("extracted_details") or {}).get("title")
        scan.extracted_company = (state.get("extracted_details") or {}).get("company")
        scan.extracted_mode = (state.get("extracted_details") or {}).get("mode")
        scan.extracted_stipend = (state.get("extracted_details") or {}).get("stipend")
        scan.extracted_duration = (state.get("extracted_details") or {}).get("duration")
        scan.extracted_skills = (state.get("extracted_details") or {}).get("skills") or []
        scan.trust_score = int(state.get("trust_score") or 0)
        scan.scam_likelihood = int(state.get("scam_likelihood") or 0)
        scan.risk_level = state.get("risk_level") or RiskLevel.needs_manual_verification.value
        scan.confidence = state.get("confidence") or ConfidenceLevel.low.value
        scan.summary = (state.get("final_result") or {}).get("summary") or state.get("summary")
        scan.green_flags = state.get("green_flags") or []
        scan.red_flags = state.get("red_flags") or []
        scan.missing_information = state.get("missing_information") or []
        scan.verification_signals = state.get("verification_signals") or {}
        scan.recommended_action = state.get("recommended_action") or scan.recommended_action
        scan.safe_message = state.get("safe_message") or scan.safe_message
        scan.agent_trace = state.get("agent_trace") or []
        scan.raw_llm_output = state.get("llm_analysis") or None
        scan.source_results = state.get("source_results") or None
        scan.final_result = state.get("final_result") or None
        return self.repository.save(db, scan)

    def _invoke_graph(self, state: PrismAgentState, thread_id: str, resume: dict[str, str] | None = None) -> PrismAgentState:
        config = {"configurable": {"thread_id": thread_id}}
        if resume is not None:
            result = self.graph.invoke(Command(resume=resume), config=config)
        else:
            result = self.graph.invoke(state, config=config)
        if isinstance(result, dict):
            return result
        return state

    def start_scan(self, db: Session, text: str | None, url: str | None, category: str = "internship") -> ScanCreateResponse:
        request = ScanCreateRequest(text=text, url=url, category=category)
        scan = self._seed_scan(db, request)
        state: PrismAgentState = {
            "scan_id": str(scan.id),
            "input_text": request.text or "",
            "input_url": request.url,
            "category": request.category,
            "workflow_status": WorkflowStatus.running.value,
            "graph_thread_id": str(scan.id),
            "graph_checkpoint_id": None,
            "review_count": 0,
            "deeper_scan_attempts": 0,
            "agent_trace": [],
        }
        result = self._invoke_graph(state, str(scan.id))
        scan = self._state_to_scan(db, scan, result)
        return _response_from_state(result, scan)

    def resume_scan(self, db: Session, scan_id: UUID, decision: str, notes: str | None = None) -> ScanCreateResponse:
        scan = self.repository.get(db, scan_id)
        if not scan:
            raise ValueError("Scan not found")
        state: PrismAgentState = {
            "scan_id": str(scan.id),
            "input_text": scan.input_text or "",
            "input_url": scan.input_url,
            "category": scan.category,
            "fetched_text": scan.fetched_text,
            "combined_text": "\n".join(part for part in [scan.input_text or "", scan.fetched_text or ""] if part),
            "extracted_details": {
                "title": scan.extracted_title,
                "company": scan.extracted_company,
                "mode": scan.extracted_mode,
                "stipend": scan.extracted_stipend,
                "duration": scan.extracted_duration,
                "skills": scan.extracted_skills or [],
            },
            "green_flags": scan.green_flags or [],
            "red_flags": scan.red_flags or [],
            "missing_information": scan.missing_information or [],
            "verification_signals": scan.verification_signals or {},
            "llm_analysis": scan.raw_llm_output or {},
            "trust_score": scan.trust_score,
            "scam_likelihood": scan.scam_likelihood,
            "risk_level": scan.risk_level,
            "confidence": scan.confidence,
            "requires_human_review": scan.requires_human_review,
            "human_review_reason": scan.human_review_reason or [],
            "human_review_payload": None,
            "human_decision": scan.human_decision,
            "human_notes": scan.human_notes,
            "recommended_action": scan.recommended_action or "",
            "safe_message": scan.safe_message or "",
            "agent_trace": scan.agent_trace or [],
            "final_result": scan.final_result or {},
            "company_verification_sources": scan.source_results.get("results", []) if isinstance(scan.source_results, dict) else [],
            "source_results": scan.source_results,
            "duplicate_copy_paste_signals": {},
            "fee_payment_risk_signals": {},
            "unrealistic_claim_signals": {},
            "recruiter_contact_risk_signals": {},
            "workflow_status": scan.workflow_status,
            "review_count": 1,
            "deeper_scan_attempts": 0,
            "graph_thread_id": scan.graph_thread_id or str(scan.id),
            "graph_checkpoint_id": scan.checkpoint_id,
        }
        result = self._invoke_graph(state, scan.graph_thread_id or str(scan.id), resume={"decision": decision, "notes": notes or ""})
        result["human_decision"] = decision
        result["human_notes"] = notes
        result["requires_human_review"] = False
        result["workflow_status"] = WorkflowStatus.rejected.value if decision == "reject_opportunity" else WorkflowStatus.completed.value
        scan = self._state_to_scan(db, scan, result)
        return _response_from_state(result, scan)

    def snapshot_scan(self, scan: Scan) -> ScanCreateResponse:
        return _snapshot_scan_response(scan)


_agent: PrismAgent | None = None


def get_agent() -> PrismAgent:
    global _agent
    if _agent is None:
        _agent = PrismAgent(get_settings())
    return _agent


def start_scan(db: Session, text: str | None, url: str | None, category: str = "internship") -> ScanCreateResponse:
    return get_agent().start_scan(db, text, url, category)


def resume_scan(db: Session, scan_id: UUID, decision: str, notes: str | None = None) -> ScanCreateResponse:
    return get_agent().resume_scan(db, scan_id, decision, notes)


def snapshot_scan(scan: Scan) -> ScanCreateResponse:
    return _snapshot_scan_response(scan)
