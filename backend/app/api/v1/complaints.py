"""Complaints API — Public Signal Intelligence endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app import demo_data
from app.runtime_store import all_signals

router = APIRouter()


def _signal_as_complaint(sig: dict[str, Any]) -> dict[str, Any]:
    return demo_data._signal_as_complaint(sig)


@router.get("")
@router.get("/")
async def list_complaints(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sentiment: str | None = None,
    source: str | None = None,
):
    """List complaints with filtering and pagination."""
    items = [_signal_as_complaint(s) for s in all_signals()]
    if sentiment:
        items = [item for item in items if item["sentiment"] == sentiment]
    if source:
        items = [item for item in items if item["source"].lower() == source.lower()]
    return demo_data.list_response(items, page, size)


@router.get("/stream/live")
async def stream_complaints():
    """SSE endpoint for live complaint feed."""
    from sse_starlette.sse import EventSourceResponse
    from app.core.events import event_dispatcher

    return EventSourceResponse(event_dispatcher.sse_stream("complaints"))


@router.get("/{complaint_id}")
async def get_complaint(complaint_id: int):
    """Get a single complaint by ID."""
    for sig in all_signals():
        if sig["id"] == complaint_id:
            return demo_data._signal_as_complaint(sig)
    raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' tidak ditemukan")


@router.post("/scrape")
async def trigger_scraping(
    source: str = Query(..., description="Social media platform to scrape"),
):
    """Delegasi ke intake scraper (fixture/live). Parameter source retained for compatibility."""
    from app.api.v1.intake import trigger_scrape
    result = await trigger_scrape()
    result["requested_source"] = source
    return result
