"""ScoreResult ORM model — stores hybrid scoring engine outputs."""

from datetime import datetime, timezone

from sqlalchemy import Integer, Float, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScoreResult(Base):
    __tablename__ = "score_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    report_id: Mapped[int] = mapped_column(Integer, index=True)  # Can reference reports or daily_reports
    report_type: Mapped[str] = mapped_column(String(20))  # "official" or "daily"

    # Scores
    severity_score: Mapped[float | None] = mapped_column(Float)
    severity_level: Mapped[str | None] = mapped_column(String(20))  # low, medium, high, critical
    confidence_score: Mapped[float | None] = mapped_column(Float)

    # Cost plausibility
    cost_per_portion: Mapped[float | None] = mapped_column(Float)
    cost_deviation_percent: Mapped[float | None] = mapped_column(Float)
    is_cost_plausible: Mapped[bool | None] = mapped_column(default=None)

    # Contributing factors (JSON array of strings)
    contributing_factors: Mapped[list | None] = mapped_column(JSON)

    # Timestamps
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
