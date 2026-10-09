from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

from app.core.config import get_settings
from app.data_loader import load_dataset


ALLOWED_UPLOAD_SUFFIXES = {".csv", ".json", ".xlsx", ".xls"}
settings = get_settings()


async def load_dataframe_from_upload(upload: UploadFile) -> tuple[pd.DataFrame, str, str]:
    """Save an uploaded file to a temporary path, then load it with the shared data loader."""

    if not upload.filename:
        raise ValueError("Please upload a file with a real filename.")

    if upload.content_type is not None and upload.content_type not in {"text/csv", "application/json", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel", "text/plain", "application/octet-stream"}:
        raise ValueError("Unsupported file type. Please upload a CSV, Excel, or JSON file.")

    upload_path = Path(upload.filename)
    suffix = upload_path.suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_SUFFIXES))
        raise ValueError(f"Unsupported file type '{suffix}'. Supported formats are: {allowed}.")

    content = await upload.read()
    if not content:
        raise ValueError("The uploaded file is empty.")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise ValueError(f"The uploaded file is too large. Please keep it under {settings.max_upload_mb} MB.")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        frame = load_dataset(temp_path)
        dataset_name = upload_path.stem
        return frame, dataset_name, suffix.lstrip(".")
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def infer_column_types(frame: pd.DataFrame) -> dict[str, str]:
    """Return friendly column type labels for the upload response."""

    column_types: dict[str, str] = {}
    for column in frame.columns:
        series = frame[column]
        if pd.api.types.is_numeric_dtype(series):
            column_types[column] = "numeric"
        elif pd.api.types.is_bool_dtype(series):
            column_types[column] = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(series):
            column_types[column] = "datetime"
        else:
            column_types[column] = "categorical"
    return column_types
