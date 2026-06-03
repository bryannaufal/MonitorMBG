"""Report schemas — request/response DTOs for official reports."""

from datetime import datetime
from pydantic import BaseModel


class ReportBase(BaseModel):
    """Shared official report fields."""
    title: str
    description: str | None = None
    region: str
    institution: str | None = None
    budget_reported: float | None = None
    portions_reported: int | None = None


class ReportCreate(ReportBase):
    """Schema for creating an official report."""
    pass


class ReportResponse(ReportBase):
    """Schema for official report API responses."""
    id: int
    document_url: str | None = None
    ocr_extracted_text: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Paginated list of reports."""
    items: list[ReportResponse] = []
    total: int = 0
    page: int = 1
    size: int = 20
