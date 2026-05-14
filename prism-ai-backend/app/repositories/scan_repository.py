from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.scan import Scan


class ScanRepository:
    def create(self, db: Session, scan: Scan) -> Scan:
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan

    def get(self, db: Session, scan_id: UUID) -> Scan | None:
        stmt: Select[tuple[Scan]] = select(Scan).where(Scan.id == scan_id)
        return db.scalar(stmt)

    def list(self, db: Session, skip: int = 0, limit: int = 20) -> tuple[list[Scan], int]:
        count_stmt = select(func.count()).select_from(Scan)
        total = db.scalar(count_stmt) or 0
        stmt = select(Scan).order_by(desc(Scan.created_at)).offset(skip).limit(limit)
        items = list(db.scalars(stmt).all())
        return items, int(total)

    def save(self, db: Session, scan: Scan) -> Scan:
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan
