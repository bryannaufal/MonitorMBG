"""Nutrition calculator — maps detected food items to calorie/macronutrient estimates."""

from typing import Any

from app.utils.constants import DEFAULT_NUTRITION_DB


class NutritionCalculator:
    """
    Calculates calorie and macronutrient estimates from detected food items.

    Uses a lookup database mapping food item names to per-100g nutritional values,
    then scales by estimated portion size.
    """

    def __init__(self, nutrition_db: dict[str, dict] | None = None):
        self.nutrition_db = nutrition_db or DEFAULT_NUTRITION_DB

    def calculate_item(
        self, food_name: str, portion_grams: float
    ) -> dict[str, float]:
        """
        Calculate nutrition for a single food item.

        Args:
            food_name: Name of the detected food item
            portion_grams: Estimated portion size in grams

        Returns:
            {"calories": float, "protein_g": float, "carbs_g": float, "fat_g": float}
        """
        # Fuzzy match food name to nutrition DB
        food_key = self._match_food_name(food_name)
        if food_key is None:
            return {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}

        ref = self.nutrition_db[food_key]
        scale = portion_grams / 100.0

        return {
            "calories": round(ref["calories"] * scale, 1),
            "protein_g": round(ref["protein"] * scale, 1),
            "carbs_g": round(ref["carbs"] * scale, 1),
            "fat_g": round(ref["fat"] * scale, 1),
        }

    def calculate_plate(
        self, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Calculate total nutrition for all items on a plate.

        Args:
            items: List of {"name": str, "portion_grams": float}

        Returns:
            {
                "items": [...per-item nutrition],
                "total": {"calories": float, ...},
                "composition": {"rice": 40%, ...}
            }
        """
        item_results = []
        totals = {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}

        for item in items:
            nutrition = self.calculate_item(item["name"], item.get("portion_grams", 100))
            item_results.append({
                "food_item": item["name"],
                "portion_grams": item.get("portion_grams", 100),
                **nutrition,
            })
            for key in totals:
                totals[key] += nutrition[key]

        # Round totals
        totals = {k: round(v, 1) for k, v in totals.items()}

        # Compute composition percentages by calorie contribution
        composition = {}
        if totals["calories"] > 0:
            for result in item_results:
                name = result["food_item"]
                composition[name] = round(
                    (result["calories"] / totals["calories"]) * 100, 1
                )

        return {
            "items": item_results,
            "total": totals,
            "composition": composition,
        }

    def _match_food_name(self, name: str) -> str | None:
        """Fuzzy-match a detected food name to the nutrition DB."""
        name_lower = name.lower().strip()

        # Exact match
        if name_lower in self.nutrition_db:
            return name_lower

        # Partial match
        for key in self.nutrition_db:
            if key in name_lower or name_lower in key:
                return key

        return None


# ── Singleton ──
nutrition_calculator = NutritionCalculator()
