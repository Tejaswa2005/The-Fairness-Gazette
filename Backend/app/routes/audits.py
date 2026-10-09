from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.fairness_engine import audit_fairness, mitigate_fairness
from app.models import AuditVerdict, get_db
from app.routes.utils import load_dataframe_from_upload
from app.schemas import AppealResponse, AuditResult, FairnessMetrics, MitigationSnapshot


router = APIRouter(tags=["audits"])


def _build_mitigation_snapshot(payload: dict[str, Any]) -> MitigationSnapshot:
	return MitigationSnapshot(
		metrics=FairnessMetrics.model_validate(payload["metrics"]),
		fairness_score=float(payload["fairness_score"]),
		verdict=str(payload["verdict"]),
		editor_note=str(payload["editor_note"]),
	)


@router.post("/audit", response_model=AuditResult)
async def run_audit(
	file: UploadFile = File(...),
	sensitive_feature: str = Form(...),
	target_column: str = Form("approved"),
	dataset_name: str | None = Form(None),
	db: Session = Depends(get_db),
) -> AuditResult:
	"""Run the fairness audit, save the verdict, and return the stored record."""

	try:
		frame, uploaded_dataset_name, _ = await load_dataframe_from_upload(file)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	resolved_dataset_name = dataset_name or uploaded_dataset_name

	try:
		result = audit_fairness(
			frame,
			sensitive_feature=sensitive_feature,
			target_column=target_column,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

	baseline = result["baseline"]
	record = AuditVerdict(
		dataset_name=resolved_dataset_name,
		sensitive_feature=sensitive_feature,
		fairness_score=float(baseline["fairness_score"]),
		verdict=str(baseline["verdict"]),
		editor_note=str(baseline["editor_note"]),
		metrics=baseline["metrics"],
	)
	db.add(record)
	db.commit()
	db.refresh(record)

	return AuditResult.model_validate(record)


@router.post("/appeal", response_model=AppealResponse)
async def run_appeal(
	file: UploadFile = File(...),
	sensitive_feature: str = Form(...),
	target_column: str = Form("approved"),
	dataset_name: str | None = Form(None),
) -> AppealResponse:
	"""Run the mitigation workflow and return the before/after comparison."""

	try:
		frame, uploaded_dataset_name, _ = await load_dataframe_from_upload(file)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

	_ = dataset_name or uploaded_dataset_name

	try:
		result = mitigate_fairness(
			frame,
			sensitive_feature=sensitive_feature,
			target_column=target_column,
		)
	except ValueError as exc:
		raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

	return AppealResponse(
		before=_build_mitigation_snapshot(result["before"]),
		after=_build_mitigation_snapshot(result["after"]),
		improvement={
			key: float(value)
			for key, value in result["improvement"].items()
		},
	)