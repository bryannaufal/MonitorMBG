"""Evidence review API — multimodal pre-verification demo records."""

from fastapi import APIRouter, Query

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_evidence(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    evidence_type: str | None = None,
    case_id: str | None = None,
):
    """List evidence objects with optional type and case filters."""
    items = demo_data.EVIDENCE
    if evidence_type:
        items = [item for item in items if item["type"].lower() == evidence_type.lower()]
    if case_id:
        items = [item for item in items if item["case_id"] == case_id]
    return demo_data.list_response(items, page, size)


@router.get("/{evidence_id}")
async def get_evidence(evidence_id: int):
    """Get a single evidence object."""
    return demo_data.get_or_404(demo_data.EVIDENCE, evidence_id, "Evidence")
