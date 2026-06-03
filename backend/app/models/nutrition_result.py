"""NutritionResult ORM model — stores food detection and nutrition estimation outputs."""

from datetime import datetime, timezone

from sqlalchemy import Integer, Float, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NutritionResult(Base):
    __tablename__ = "nutrition_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    daily_report_id: Mapped[int] = mapped_column(Integer, ForeignKey("daily_reports.id"), index=True)
    photo_url: Mapped[str | None] = mapped_column(String(500))

    # Detected food items (JSON array of {name, confidence, bbox, portion_grams})
    detected_items: Mapped[list | None] = mapped_column(JSON)

    # Total nutrition
    total_calories: Mapped[float | None] = mapped_column(Float)
    total_protein_g: Mapped[float | None] = mapped_column(Float)
    total_carbs_g: Mapped[float | None] = mapped_column(Float)
    total_fat_g: Mapped[float | None] = mapped_column(Float)

    # Menu composition (JSON: {"rice": 40, "protein": 30, ...})
    menu_composition: Mapped[dict | None] = mapped_column(JSON)
    meets_standard: Mapped[bool | None] = mapped_column(default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
