from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas import UploadResponse
from app.routes.utils import infer_column_types, load_dataframe_from_upload


router = APIRouter(tags=["uploads"])


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> UploadResponse:
    """Validate an uploaded dataset and return its detected columns."""

    try:
        frame, dataset_name, file_type = await load_dataframe_from_upload(file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - safety net for unexpected failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The uploaded file could not be processed.",
        ) from exc

    return UploadResponse(
        dataset_name=dataset_name,
        file_type=file_type,
        row_count=int(frame.shape[0]),
        columns=list(frame.columns),
        column_types=infer_column_types(frame),
        preview_rows=frame.head(5).to_dict(orient="records"),
    )
