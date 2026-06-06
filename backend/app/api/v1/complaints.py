"""Complaints API — Public Signal Intelligence endpoints."""

from fastapi import APIRouter, Query

from app import demo_data

router = APIRouter()


@router.get("")
@router.get("/")
async def list_complaints(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sentiment: str | None = None,
    source: str | None = None,
):
    """List complaints with filtering and pagination."""
    items = demo_data.COMPLAINTS
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
    return demo_data.get_or_404(demo_data.COMPLAINTS, complaint_id, "Complaint")


@router.post("/scrape")
async def trigger_scraping(
    source: str = Query(..., description="Social media platform to scrape"),
):
    """Return a safe demo response for scraping.

    Real scraping is intentionally not performed in the MVP.
    """
    return {
        "message": f"Demo scraping simulation for '{source}' queued.",
        "task_id": "demo-scrape",
        "ai_notice": demo_data.DEMO_NOTICE,
    }
