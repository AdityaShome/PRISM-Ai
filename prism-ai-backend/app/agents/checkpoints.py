from __future__ import annotations

from app.core.config import Settings

try:  # pragma: no cover - optional backend-specific saver
    from langgraph.checkpoint.postgres import PostgresSaver
except Exception:  # pragma: no cover - fallback when saver package changes
    PostgresSaver = None

try:
    from langgraph.checkpoint.memory import MemorySaver
except Exception as exc:  # pragma: no cover - hard dependency
    raise RuntimeError("LangGraph MemorySaver is required") from exc


def build_checkpointer(settings: Settings):
    if PostgresSaver and settings.database_url.startswith(("postgresql", "postgres")):
        try:
            checkpointer = PostgresSaver.from_conn_string(settings.database_url)
            if hasattr(checkpointer, "setup"):
                checkpointer.setup()
            return checkpointer
        except Exception:
            pass
    return MemorySaver()
