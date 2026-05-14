from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scan import Scan
from app.repositories.scan_repository import ScanRepository
from app.schemas.common import ScanListItem, ScanListResponse
from app.schemas.scan import ReviewDecisionRequest, RescanRequest, ScanCreateRequest, ScanCreateResponse
from app.agents.prism_agent import resume_scan, snapshot_scan, start_scan

router = APIRouter(prefix="/api/scans", tags=["scans"])
scan_repository = ScanRepository()


def _to_list_item(scan: Scan) -> ScanListItem:
    return ScanListItem(
        id=scan.id,
        created_at=scan.created_at.isoformat(),
        risk_level=scan.risk_level,
        trust_score=scan.trust_score,
        summary=scan.summary,
        extracted_title=scan.extracted_title,
        extracted_company=scan.extracted_company,
        category=scan.category,
    )


@router.post("", response_model=ScanCreateResponse)
def create_scan(payload: ScanCreateRequest, db: Session = Depends(get_db)) -> ScanCreateResponse:
    return start_scan(db, payload.text, payload.url, payload.category)


@router.get("", response_model=ScanListResponse)
def list_scans(skip: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100), db: Session = Depends(get_db)) -> ScanListResponse:
    items, total = scan_repository.list(db, skip=skip, limit=limit)
    return ScanListResponse(items=[_to_list_item(item) for item in items], total=total, skip=skip, limit=limit)


@router.get("/{scan_id}", response_model=ScanCreateResponse)
def get_scan(scan_id: UUID, db: Session = Depends(get_db)) -> ScanCreateResponse:
    scan = scan_repository.get(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return snapshot_scan(scan)


@router.post("/{scan_id}/rescan", response_model=ScanCreateResponse)
def rescan_scan(scan_id: UUID, payload: RescanRequest | None = None, db: Session = Depends(get_db)) -> ScanCreateResponse:
    scan = scan_repository.get(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    text = payload.text if payload and payload.text is not None else scan.input_text
    url = payload.url if payload and payload.url is not None else scan.input_url
    category = payload.category if payload and payload.category else scan.category
    return start_scan(db, text, url, category)


@router.post("/{scan_id}/review", response_model=ScanCreateResponse)
def review_scan(scan_id: UUID, payload: ReviewDecisionRequest, db: Session = Depends(get_db)) -> ScanCreateResponse:
    try:
        return resume_scan(db, scan_id, payload.decision, payload.notes)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
