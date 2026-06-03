"""Daily Report schemas — request/response DTOs for photo-verified reports."""

from datetime import datetime
from pydantic import BaseModel

from app.utils.constants import VerificationStatus


class DailyReportBase(BaseModel):
    """Shared daily report fields."""
    title: str
    description: str | None = None
    region: str
    school_name: str | None = None
    menu_description: str | None = None
    portions_served: int | None = None
    cost_reported: float | None = None


class DailyReportCreate(DailyReportBase):
    """Schema for creating a daily report."""
    pass


class PhotoVerification(BaseModel):
    """Verification result for an uploaded photo."""
    photo_url: str
    perceptual_hash: str | None = None
    is_duplicate: bool = False
    duplicate_of_report_id: int | None = None
    image_text_similarity: float | None = None


class DailyReportResponse(DailyReportBase):
    """Schema for daily report API responses."""
    id: int
    verification_status: VerificationStatus = VerificationStatus.PENDING
    photo_urls: list[str] = []
    photo_verifications: list[PhotoVerification] = []
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class DailyReportListResponse(BaseModel):
    """Paginated list of daily reports."""
    items: list[DailyReportResponse] = []
    total: int = 0
    page: int = 1
    size: int = 20
