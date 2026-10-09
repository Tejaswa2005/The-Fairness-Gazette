from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models import init_db
from app.routes import router as api_router


settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("fairness-gazette")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize the SQLite schema before the API starts serving traffic."""

    logger.info("Initializing database and application lifespan.")
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, description="FastAPI backend for fairness audits, verdict storage, and mitigation reports.", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def health_check() -> dict[str, str]:
    """Simple health check for local and deployment probes."""

    logger.debug("Health check requested.")
    return {
        "status": "ok",
        "message": "THE FAIRNESS GAZETTE backend is running.",
    }
