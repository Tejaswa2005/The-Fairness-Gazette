from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditVerdict, get_db
from app.schemas import VerdictHistoryResponse, VerdictRecord


router = APIRouter(tags=["verdicts"])


def _to_verdict_record(row: AuditVerdict) -> VerdictRecord:
    return VerdictRecord.model_validate(row)


@router.get("/verdicts", response_model=VerdictHistoryResponse)
def list_verdicts(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> VerdictHistoryResponse:
    """Return saved verdicts from newest to oldest."""

    rows = db.execute(select(AuditVerdict).order_by(AuditVerdict.created_at.desc()).limit(limit)).scalars().all()
    return VerdictHistoryResponse(items=[_to_verdict_record(row) for row in rows])


@router.get("/verdicts/{verdict_id}", response_model=VerdictRecord)
def get_verdict(verdict_id: int, db: Session = Depends(get_db)) -> VerdictRecord:
    """Return a single saved verdict by primary key."""

    row = db.get(AuditVerdict, verdict_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Verdict not found.")
    return _to_verdict_record(row)
