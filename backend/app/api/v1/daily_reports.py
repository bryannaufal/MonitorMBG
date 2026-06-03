"""Daily Reports API — Photo-verified daily report endpoints."""

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.daily_report import DailyReportCreate, DailyReportResponse, DailyReportListResponse

router = APIRouter()


@router.get("/", response_model=DailyReportListResponse)
async def list_daily_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    verification_status: str | None = None,
    region: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List daily reports with filtering by verification status and region."""
    # TODO: Implement via daily_report_service
    return {"items": [], "total": 0, "page": page, "size": size}


@router.post("/", response_model=DailyReportResponse)
async def create_daily_report(
    report: DailyReportCreate,
    session: AsyncSession = Depends(get_session),
):
    """Submit a new daily report."""
    # TODO: Implement via daily_report_service
    return {}


@router.post("/{report_id}/photos")
async def upload_photos(
    report_id: int,
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
):
    """
    Upload photos for a daily report.

    Triggers:
    - Perceptual hash computation (duplicate detection)
    - Image-text similarity matching
    - Food detection + nutrition estimation pipeline
    """
    # TODO: Dispatch CV pipeline tasks via Celery
    # from app.workers.cv_tasks import process_daily_report_images
    # task = process_daily_report_images.delay(report_id, [file paths])
    return {
        "message": f"{len(files)} photo(s) uploaded. Verification pipeline dispatched.",
        "report_id": report_id,
    }


@router.get("/{report_id}/verification")
async def get_verification_status(
    report_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get the multimodal verification status for a daily report."""
    # TODO: Return verification results (hash match, image-text similarity, etc.)
    return {"report_id": report_id, "status": "pending", "results": {}}
