from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    """Response returned after a file is uploaded and validated."""

    dataset_name: str
    file_type: str
    row_count: int
    columns: list[str]
    column_types: dict[str, str]
    preview_rows: list[dict[str, Any]] = Field(default_factory=list)


class AuditRequest(BaseModel):
    """Normalized request data used when running a fairness audit."""

    dataset_name: str | None = None
    sensitive_feature: str
    target_column: str = "approved"


class AppealRequest(BaseModel):
    """Normalized request data used when running mitigation."""

    dataset_name: str | None = None
    sensitive_feature: str
    target_column: str = "approved"


class FairnessMetrics(BaseModel):
    """Structured fairness metrics returned by the engine."""

    demographic_parity_difference: float
    equalized_odds_difference: float
    selection_rate_by_group: dict[str, float]
    selection_rate_spread: float


class VerdictRecord(BaseModel):
    """A single stored verdict row as it is returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_name: str
    sensitive_feature: str
    fairness_score: float
    verdict: str
    editor_note: str
    metrics: dict[str, Any]
    created_at: datetime


class AuditResult(VerdictRecord):
    """Audit response for a newly saved verdict."""


class MitigationSnapshot(BaseModel):
    """Before/after result for the appeal endpoint."""

    metrics: FairnessMetrics
    fairness_score: float
    verdict: str
    editor_note: str


class AppealResponse(BaseModel):
    """Full mitigation comparison returned by the appeal endpoint."""

    before: MitigationSnapshot
    after: MitigationSnapshot
    improvement: dict[str, float]


class VerdictHistoryResponse(BaseModel):
    """Wrapper for a verdict history listing."""

    items: list[VerdictRecord]
