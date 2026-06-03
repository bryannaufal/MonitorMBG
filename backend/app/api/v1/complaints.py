"""Complaints API — Public Signal Intelligence endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.complaint import ComplaintResponse, ComplaintListResponse

router = APIRouter()


@router.get("/", response_model=ComplaintListResponse)
async def list_complaints(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sentiment: str | None = None,
    source: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """List complaints with filtering and pagination."""
    # TODO: Implement via complaint_service
    return {"items": [], "total": 0, "page": page, "size": size}


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Get a single complaint by ID."""
    # TODO: Implement via complaint_service
    return {}


@router.post("/scrape")
async def trigger_scraping(
    source: str = Query(..., description="Social media platform to scrape"),
):
    """Trigger an on-demand social media scraping task."""
    # TODO: Dispatch Celery task
    # from app.workers.scraping_tasks import scrape_social_media
    # task = scrape_social_media.delay(source)
    return {"message": f"Scraping task for '{source}' dispatched", "task_id": "pending"}


@router.get("/stream/live")
async def stream_complaints():
    """SSE endpoint for live complaint feed."""
    # TODO: Implement SSE stream via event_dispatcher
    from sse_starlette.sse import EventSourceResponse
    from app.core.events import event_dispatcher

    return EventSourceResponse(event_dispatcher.sse_stream("complaints"))
