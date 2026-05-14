from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TraceStatus(str, Enum):
    completed = "completed"
    warning = "warning"
    failed = "failed"
    skipped = "skipped"
    awaiting_review = "awaiting_review"


class WorkflowStatus(str, Enum):
    pending = "pending"
    running = "running"
    awaiting_human_review = "awaiting_human_review"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"


class RiskLevel(str, Enum):
    low_risk = "Low Risk"
    medium_risk = "Medium Risk"
    high_caution = "High Caution"
    high_risk = "High Risk"
    needs_manual_verification = "Needs Manual Verification"


class ConfidenceLevel(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class UserRating(str, Enum):
    helpful = "helpful"
    not_helpful = "not_helpful"


class FlagItem(BaseModel):
    label: str
    evidence: str
    severity: Severity | None = None


class ExtractedDetails(BaseModel):
    title: str | None = None
    company: str | None = None
    role_type: str | None = None
    stipend: str | None = None
    mode: str | None = None
    duration: str | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)
    contact_method: str | None = None
    application_channel: str | None = None
    application_fee: bool | None = None
    deadline: str | None = None
    suspicious_phrases: list[str] = Field(default_factory=list)
    recruiter_email: str | None = None


class VerificationSignals(BaseModel):
    company_website_found: bool | None = None
    official_domain_match: bool | None = None
    company_footprint: str | None = None
    duplicate_post_risk: str | None = None
    search_results_checked: int = 0
    suspicious_source_notes: list[str] = Field(default_factory=list)


class TraceStep(BaseModel):
    step: str
    label: str
    status: TraceStatus
    detail: str | None = None
    timestamp: str | None = None


class HumanReviewPayload(BaseModel):
    type: str = "human_review_required"
    scan_id: str
    message: str
    trust_score: int
    risk_level: str
    confidence: str
    review_reasons: list[str] = Field(default_factory=list)
    green_flags: list[FlagItem] = Field(default_factory=list)
    red_flags: list[FlagItem] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=lambda: [
        "run_deeper_scan",
        "generate_safe_message",
        "mark_suspicious",
        "continue_anyway",
        "reject_opportunity",
    ])


class HumanReviewDecision(BaseModel):
    decision: str
    notes: str | None = None


class HumanReviewResponse(BaseModel):
    message: str
    review_reasons: list[str] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)


class SearchSource(BaseModel):
    title: str
    url: str | None = None
    snippet: str | None = None
    source_type: str | None = None


class ComingSoonCategory(BaseModel):
    category: str
    status: str = "coming_soon"
    message: str
    supported: bool = False


class ScanListItem(BaseModel):
    id: UUID
    created_at: str
    risk_level: str
    trust_score: int
    summary: str | None = None
    extracted_title: str | None = None
    extracted_company: str | None = None
    category: str


class ScanListResponse(BaseModel):
    items: list[ScanListItem]
    total: int
    skip: int
    limit: int


class ApiMessage(BaseModel):
    message: str
    detail: str | None = None
