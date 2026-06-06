"""Daily Reports API — Photo-verified daily report endpoints."""

from fastapi import APIRouter, File, Query, UploadFile

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_daily_reports(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    verification_status: str | None = None,
    region: str | None = None,
):
    """List daily reports with filtering by verification status and region."""
    items = demo_data.DAILY_REPORTS
    if verification_status:
        items = [item for item in items if item["verification_status"].lower() == verification_status.lower()]
    if region:
        items = [item for item in items if item["region"].lower() == region.lower()]
    return demo_data.list_response(items, page, size)


@router.get("/{report_id}")
async def get_daily_report(report_id: int):
    """Get a single daily report by ID."""
    return demo_data.get_or_404(demo_data.DAILY_REPORTS, report_id, "Daily report")


@router.post("/{report_id}/photos")
async def upload_photos(
    report_id: int,
    files: list[UploadFile] = File(...),
):
    """
    Upload photos for a daily report.

    Triggers:
    - Perceptual hash computation (duplicate detection)
    - Image-text similarity matching
    - Food detection + nutrition estimation pipeline
    """
    demo_data.get_or_404(demo_data.DAILY_REPORTS, report_id, "Daily report")
    return {
        "message": f"{len(files)} photo(s) accepted for simulated CV pre-verification.",
        "report_id": report_id,
        "ai_notice": demo_data.DEMO_NOTICE,
    }


@router.get("/{report_id}/verification")
async def get_verification_status(
    report_id: int,
):
    """Get the multimodal verification status for a daily report."""
    report = demo_data.get_or_404(demo_data.DAILY_REPORTS, report_id, "Daily report")
    evidence = [item for item in demo_data.EVIDENCE if item["report_id"] == report_id]
    return {
        "report_id": report_id,
        "status": report["verification_status"],
        "results": {
            "photo_verification": report["photo_verification"],
            "duplicate_indicator": report["duplicate_indicator"],
            "mismatch_indicator": report["mismatch_indicator"],
            "document_complete": report["document_complete"],
            "evidence": evidence,
        },
        "ai_notice": demo_data.DEMO_NOTICE,
    }
