from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generator

from sqlalchemy import JSON, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.core.config import get_settings


settings = get_settings()
DATABASE_URL = settings.database_url


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in the application."""


class AuditVerdict(Base):
    """Stores a saved fairness audit verdict and the key metrics behind it."""

    __tablename__ = "audit_verdicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sensitive_feature: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    fairness_score: Mapped[float] = mapped_column(nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    editor_note: Mapped[str] = mapped_column(String(2000), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(timezone.utc),
    )


def init_db() -> None:
    """Create application tables if they do not already exist."""

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and make sure it is closed afterward."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()