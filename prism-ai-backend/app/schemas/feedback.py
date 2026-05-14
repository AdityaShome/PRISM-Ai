from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import UserRating


class FeedbackCreateRequest(BaseModel):
    scan_id: str = Field(...)
    user_rating: UserRating
    user_comment: str | None = None


class FeedbackResponse(BaseModel):
    id: str
    scan_id: str
    user_rating: UserRating
    user_comment: str | None = None
