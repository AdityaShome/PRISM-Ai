from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, GUID


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[object] = mapped_column(GUID(), primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="internship", nullable=False)
    workflow_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    human_review_reason: Mapped[list[str] | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    human_decision: Mapped[str | None] = mapped_column(String(80), nullable=True)
    human_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    graph_thread_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    checkpoint_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    review_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    extracted_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_mode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extracted_stipend: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extracted_duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extracted_skills: Mapped[list[str] | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)

    trust_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scam_likelihood: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(80), default="Needs Manual Verification", nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), default="Low", nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    green_flags: Mapped[list[dict] | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    red_flags: Mapped[list[dict] | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    missing_information: Mapped[list[str] | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    verification_signals: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    safe_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    agent_trace: Mapped[list[dict] | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    raw_llm_output: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    source_results: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
    final_result: Mapped[dict | None] = mapped_column(JSON().with_variant(JSONB(), "postgresql"), nullable=True)
