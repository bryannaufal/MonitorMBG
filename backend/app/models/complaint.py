"""Complaint ORM model — stores scraped social media complaints."""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # twitter, instagram, etc.
    source_url: Mapped[str | None] = mapped_column(String(500))
    author: Mapped[str | None] = mapped_column(String(200))
    region: Mapped[str | None] = mapped_column(String(100), index=True)

    # NLP results
    sentiment: Mapped[str | None] = mapped_column(String(20))
    sentiment_score: Mapped[float | None] = mapped_column(Float)
    topic_cluster: Mapped[str | None] = mapped_column(String(200))

    # Status & scoring
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    severity_score: Mapped[float | None] = mapped_column(Float)

    # Raw scraped data
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
