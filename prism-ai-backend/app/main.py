from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.categories import router as categories_router
from app.api.routes.feedback import router as feedback_router
from app.api.routes.health import router as health_router
from app.api.routes.scans import router as scans_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import SimpleRateLimitMiddleware
from app.db.base import Base
from app.db.session import engine
from app.models.feedback import Feedback  # noqa: F401
from app.models.scan import Scan  # noqa: F401

settings = get_settings()
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.auto_create_tables or settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Prism AI Backend", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SimpleRateLimitMiddleware, settings=settings)

app.include_router(health_router)
app.include_router(scans_router)
app.include_router(categories_router)
app.include_router(feedback_router)
