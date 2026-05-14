from sqlalchemy.orm import Session

from app.core.config import Settings
from app.agents.prism_agent import get_agent
from app.schemas.scan import ReviewDecisionRequest, ScanCreateRequest, ScanCreateResponse


class ScanService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.agent = get_agent()

    def run_scan(self, db: Session, request: ScanCreateRequest) -> ScanCreateResponse:
        return self.agent.start_scan(db, request.text, request.url, request.category)

    def resume_scan(self, db: Session, scan_id, decision: str, notes: str | None = None) -> ScanCreateResponse:
        return self.agent.resume_scan(db, scan_id, decision, notes)

    def snapshot_scan(self, scan) -> ScanCreateResponse:
        return self.agent.snapshot_scan(scan)
