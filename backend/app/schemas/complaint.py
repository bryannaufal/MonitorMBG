"""Complaint schemas — request/response DTOs for social listening."""

from datetime import datetime
from pydantic import BaseModel

from app.utils.constants import SentimentLabel, ComplaintSource, ComplaintStatus


class ComplaintBase(BaseModel):
    """Shared complaint fields."""
    text: str
    source: ComplaintSource
    source_url: str | None = None
    author: str | None = None
    region: str | None = None


class ComplaintCreate(ComplaintBase):
    """Schema for creating a complaint (from scraping pipeline)."""
    raw_data: dict | None = None


class ComplaintResponse(ComplaintBase):
    """Schema for complaint API responses."""
    id: int
    sentiment: SentimentLabel | None = None
    sentiment_score: float | None = None
    topic_cluster: str | None = None
    status: ComplaintStatus = ComplaintStatus.NEW
    severity_score: float | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ComplaintListResponse(BaseModel):
    """Paginated list of complaints."""
    items: list[ComplaintResponse] = []
    total: int = 0
    page: int = 1
    size: int = 20
