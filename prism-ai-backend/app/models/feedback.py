from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, GUID


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[object] = mapped_column(GUID(), primary_key=True, default=uuid4)
    scan_id: Mapped[object] = mapped_column(GUID(), ForeignKey("scans.id", ondelete="CASCADE"), nullable=False)
    user_rating: Mapped[str] = mapped_column(String(20), nullable=False)
    user_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
