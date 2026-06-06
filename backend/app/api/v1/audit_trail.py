"""Audit trail API — human-in-the-loop and AI output history."""

from fastapi import APIRouter, Query

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_audit_trail(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
):
    """List audit events."""
    items = sorted(demo_data.AUDIT_TRAIL, key=lambda item: item["timestamp"], reverse=True)
    return demo_data.list_response(items, page, size)


@router.get("/case/{case_id}")
async def get_case_audit_trail(case_id: str):
    """List audit events for a case."""
    items = [item for item in demo_data.AUDIT_TRAIL if item["case_id"] == case_id]
    return {"items": items, "total": len(items), "case_id": case_id}
