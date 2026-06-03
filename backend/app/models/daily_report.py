"""DailyReport ORM model — stores daily field reports with photo verification data."""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    school_name: Mapped[str | None] = mapped_column(String(300))
    menu_description: Mapped[str | None] = mapped_column(Text)
    portions_served: Mapped[int | None] = mapped_column(Integer)
    cost_reported: Mapped[float | None] = mapped_column(Float)

    # Photo & verification
    photo_urls: Mapped[list | None] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    photo_verifications: Mapped[dict | None] = mapped_column(JSON)  # Array of verification results

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
