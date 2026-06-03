"""Report ORM model — stores official government reports."""

from datetime import datetime, timezone

from sqlalchemy import Integer, String, Float, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    institution: Mapped[str | None] = mapped_column(String(200))
    budget_reported: Mapped[float | None] = mapped_column(Float)
    portions_reported: Mapped[int | None] = mapped_column(Integer)

    # Document / OCR
    document_url: Mapped[str | None] = mapped_column(String(500))
    ocr_extracted_text: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
