from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.schemas.common import TraceStep, TraceStatus


def build_trace(steps: list[dict[str, Any]]) -> list[TraceStep]:
    return [
        TraceStep(
            step=item["step"],
            label=item.get("label") or item["step"],
            status=item["status"],
            detail=item.get("detail"),
            timestamp=item.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        )
        for item in steps
    ]


def trace_step(
    step: str,
    status: TraceStatus | str,
    detail: str | None = None,
    label: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    return {
        "step": step,
        "label": label or step.replace("_", " ").title(),
        "status": TraceStatus(status),
        "detail": detail,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }
