from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.feedback import Feedback
from app.repositories.scan_repository import ScanRepository
from app.schemas.feedback import FeedbackCreateRequest, FeedbackResponse

router = APIRouter(prefix="/api", tags=["feedback"])
scan_repository = ScanRepository()


@router.post("/feedback", response_model=FeedbackResponse)
def create_feedback(payload: FeedbackCreateRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    scan = scan_repository.get(db, payload.scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")

    feedback = Feedback(scan_id=scan.id, user_rating=payload.user_rating.value, user_comment=payload.user_comment)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackResponse(id=str(feedback.id), scan_id=str(feedback.scan_id), user_rating=payload.user_rating, user_comment=feedback.user_comment)
