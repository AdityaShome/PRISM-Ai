from __future__ import annotations

from typing import Any, TypedDict


class PrismAgentState(TypedDict, total=False):
    scan_id: str
    input_text: str
    input_url: str | None
    category: str
    fetched_text: str | None
    combined_text: str
    extracted_details: dict[str, Any]
    green_flags: list[dict[str, Any]]
    red_flags: list[dict[str, Any]]
    missing_information: list[str]
    verification_signals: dict[str, Any]
    llm_analysis: dict[str, Any]
    trust_score: int
    scam_likelihood: int
    risk_level: str
    confidence: str
    requires_human_review: bool
    human_review_reason: list[str]
    human_review_payload: dict[str, Any] | None
    human_decision: str | None
    human_notes: str | None
    recommended_action: str
    safe_message: str
    agent_trace: list[dict[str, Any]]
    final_result: dict[str, Any]
    company_verification_sources: list[dict[str, Any]]
    source_results: dict[str, Any] | None
    duplicate_copy_paste_signals: dict[str, Any]
    fee_payment_risk_signals: dict[str, Any]
    unrealistic_claim_signals: dict[str, Any]
    recruiter_contact_risk_signals: dict[str, Any]
    workflow_status: str
    review_count: int
    deeper_scan_attempts: int
    graph_thread_id: str | None
    graph_checkpoint_id: str | None
