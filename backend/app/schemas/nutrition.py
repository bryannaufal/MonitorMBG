"""Nutrition schemas — request/response DTOs for food analysis."""

from pydantic import BaseModel


class DetectedFoodItem(BaseModel):
    """A single food item detected by the CV engine."""
    name: str
    confidence: float
    bounding_box: dict | None = None  # {x, y, width, height}
    estimated_portion_grams: float | None = None


class MacronutrientEstimate(BaseModel):
    """Macronutrient breakdown for a detected food item or full plate."""
    calories: float = 0.0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0


class FoodItemNutrition(BaseModel):
    """A detected food item with its nutrition estimate."""
    food_item: DetectedFoodItem
    nutrition: MacronutrientEstimate


class NutritionResultResponse(BaseModel):
    """Complete nutrition estimation result for a daily report."""
    report_id: int | None = None
    photo_url: str | None = None
    detected_items: list[FoodItemNutrition] = []
    total_nutrition: MacronutrientEstimate = MacronutrientEstimate()
    menu_composition: dict | None = None  # {"rice": 40%, "protein": 30%, ...}
    meets_standard: bool | None = None
    analysis_notes: str | None = None
