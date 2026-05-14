from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_prism_ai.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENABLE_LLM_ANALYSIS", "true")
os.environ.setdefault("ENABLE_WEB_SEARCH", "true")
os.environ.setdefault("ENABLE_URL_FETCH", "true")
os.environ.setdefault("LLM_PROVIDER", "gemini")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault("GEMINI_MODEL", "gemini-2.0-flash")
os.environ.setdefault("TAVILY_API_KEY", "test")
os.environ.setdefault("RATE_LIMIT_PER_MINUTE", "0")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:5173"]')

from app.agents.prism_agent import get_agent
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.feedback import Feedback
from app.models.scan import Scan
from app.services.llm_service import LLMOutcome
from app.services.search_service import SearchOutcome
from app.core.config import get_settings

get_settings.cache_clear()
agent = get_agent()


@pytest.fixture(scope="session", autouse=True)
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_database() -> None:
    with SessionLocal() as db:
        db.execute(delete(Feedback))
        db.execute(delete(Scan))
        db.commit()
    yield


@pytest.fixture(autouse=True)
def patch_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        agent.search_service,
        "search_company",
        lambda company, title=None, deep_scan=False: SearchOutcome(
            status="completed",
            results=[
                {
                    "title": f"{company} Careers | Official",
                    "url": f"https://{company.lower().replace(' ', '')}.com/careers",
                    "snippet": f"Official careers page for {company}.",
                    "source_type": "search",
                },
                {
                    "title": f"{company} on LinkedIn",
                    "url": f"https://www.linkedin.com/company/{company.lower().replace(' ', '-')}",
                    "snippet": f"Public company profile for {company}.",
                    "source_type": "search",
                },
            ],
            notes=["patched for tests"],
        ),
    )
    monkeypatch.setattr(
        agent.llm_service,
        "analyze",
        lambda combined_text, extracted_details, search_summary=None: LLMOutcome(status="skipped"),
    )
    yield


@pytest.fixture()
def prism_agent():
    return agent


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
