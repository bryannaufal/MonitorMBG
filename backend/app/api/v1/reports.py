"""Reports API — Official report management endpoints."""

from fastapi import APIRouter, File, Query, UploadFile

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    region: str | None = None,
):
    """List official reports with filtering and pagination."""
    items = demo_data.REPORTS
    if region:
        items = [item for item in items if item["region"].lower() == region.lower()]
    return demo_data.list_response(items, page, size)


@router.get("/{report_id}")
async def get_report(report_id: int):
    """Get a single official report by ID."""
    return demo_data.get_or_404(demo_data.REPORTS, report_id, "Report")


@router.post("/{report_id}/documents")
async def upload_report_document(
    report_id: int,
    file: UploadFile = File(...),
):
    """Simulate document upload and OCR pre-verification for a report."""
    demo_data.get_or_404(demo_data.REPORTS, report_id, "Report")
    return {
        "message": "Document accepted for demo OCR pre-verification.",
        "filename": file.filename,
        "report_id": report_id,
        "ocr_result": "Simulated OCR extracted invoice total, vendor name, and portion count.",
        "ai_notice": demo_data.DEMO_NOTICE,
    }
