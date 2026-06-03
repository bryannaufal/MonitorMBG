"""Nutrition API — Food nutrition estimation result endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.nutrition import NutritionResultResponse

router = APIRouter()


@router.get("/report/{report_id}", response_model=NutritionResultResponse)
async def get_nutrition_results(
    report_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get nutrition estimation results for a daily report.

    Returns detected food items, portion estimates, and
    calorie/macronutrient calculations.
    """
    # TODO: Implement via daily_report_service / nutrition results
    return {}


@router.get("/summary")
async def get_nutrition_summary(
    region: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Get aggregated nutrition summary across reports.

    Returns average calorie counts, macronutrient distribution,
    and compliance with nutritional standards.
    """
    # TODO: Implement aggregated nutrition analytics
    return {
        "avg_calories": 0,
        "avg_protein_g": 0,
        "avg_carbs_g": 0,
        "avg_fat_g": 0,
        "total_reports_analyzed": 0,
    }
