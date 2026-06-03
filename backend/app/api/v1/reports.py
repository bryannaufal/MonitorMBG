"""Reports API — Official report management endpoints."""

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.report import ReportCreate, ReportResponse, ReportListResponse

router = APIRouter()


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    region: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List official reports with filtering and pagination."""
    # TODO: Implement via report_service
    return {"items": [], "total": 0, "page": page, "size": size}


@router.post("/", response_model=ReportResponse)
async def create_report(
    report: ReportCreate,
    session: AsyncSession = Depends(get_session),
):
    """Submit a new official report."""
    # TODO: Implement via report_service
    return {}


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single official report by ID."""
    # TODO: Implement via report_service
    return {}


@router.post("/{report_id}/documents")
async def upload_report_document(
    report_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Upload a supporting document for OCR processing."""
    # TODO: Dispatch OCR task via Celery
    return {"message": "Document uploaded and OCR task dispatched", "report_id": report_id}
