from __future__ import annotations

from fastapi import APIRouter

from app.routes.audits import router as audits_router
from app.routes.uploads import router as uploads_router
from app.routes.verdicts import router as verdicts_router


router = APIRouter()
router.include_router(uploads_router)
router.include_router(audits_router)
router.include_router(verdicts_router)
