from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import (
    ConfidenceLevel,
    HumanReviewPayload,
    ExtractedDetails,
    FlagItem,
    RiskLevel,
    SearchSource,
    TraceStep,
    WorkflowStatus,
    VerificationSignals,
)


class ScanCreateRequest(BaseModel):
    text: str | None = Field(default=None, description="Raw internship post text")
    url: str | None = Field(default=None, description="Optional internship posting URL")
    category: str = Field(default="internship")

    @model_validator(mode="after")
    def validate_input(self) -> "ScanCreateRequest":
        if not self.text and not self.url:
            raise ValueError("At least one of text or url is required")
        if self.category != "internship":
            return self
        return self


class ScanCreateResponse(BaseModel):
    scan_id: UUID
    category: str
    workflow_status: WorkflowStatus | str = WorkflowStatus.completed
    requires_human_review: bool = False
    human_review: HumanReviewPayload | None = None
    human_review_reason: list[str] = Field(default_factory=list)
    human_decision: str | None = None
    human_notes: str | None = None
    graph_thread_id: str | None = None
    checkpoint_id: str | None = None
    analysis_available: bool = True
    risk_level: str
    trust_score: int | None
    scam_likelihood: int | None
    confidence: ConfidenceLevel | str
    summary: str
    extracted_details: ExtractedDetails
    green_flags: list[FlagItem] = Field(default_factory=list)
    red_flags: list[FlagItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    verification_signals: VerificationSignals
    duplicate_copy_paste_signals: dict[str, Any] = Field(default_factory=dict)
    fee_payment_risk_signals: dict[str, Any] = Field(default_factory=dict)
    unrealistic_claim_signals: dict[str, Any] = Field(default_factory=dict)
    recruiter_contact_risk_signals: dict[str, Any] = Field(default_factory=dict)
    recommended_action: str
    safe_message: str
    agent_trace: list[TraceStep] = Field(default_factory=list)
    company_verification_sources: list[SearchSource] = Field(default_factory=list)
    raw_llm_output: dict[str, Any] | None = None
    source_results: dict[str, Any] | None = None
    final_result: dict[str, Any] | None = None


class RescanRequest(BaseModel):
    text: str | None = None
    url: str | None = None
    category: str = "internship"


class ReviewDecisionRequest(BaseModel):
    decision: str
    notes: str | None = None


class ScanFeedbackResponse(BaseModel):
    message: str


class CategoryListItem(BaseModel):
    category: str
    title: str
    description: str
    supported: bool
    status: str
