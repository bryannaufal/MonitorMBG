"""Cost plausibility analysis against standard government budgets."""

from typing import Any

from app.utils.constants import STANDARD_BUDGET_PER_PORTION_IDR, BUDGET_TOLERANCE_PERCENT


class CostPlausibilityAnalyzer:
    """
    Analyzes whether reported costs per portion are plausible
    against standard government budget allocations.
    """

    def __init__(
        self,
        standard_budget: float = STANDARD_BUDGET_PER_PORTION_IDR,
        tolerance_percent: float = BUDGET_TOLERANCE_PERCENT,
    ):
        self.standard_budget = standard_budget
        self.tolerance_percent = tolerance_percent

    def analyze(
        self,
        total_cost: float,
        portions_served: int,
    ) -> dict[str, Any]:
        """
        Analyze cost plausibility for a report.

        Args:
            total_cost: Total reported cost in IDR
            portions_served: Number of portions served

        Returns:
            {
                "cost_per_portion": float,
                "standard_budget": float,
                "deviation_percent": float,
                "is_plausible": bool,
                "flag": str | None,
            }
        """
        if portions_served <= 0:
            return {
                "cost_per_portion": 0,
                "standard_budget": self.standard_budget,
                "deviation_percent": 0,
                "is_plausible": False,
                "flag": "Invalid portions count (≤ 0)",
            }

        cost_per_portion = total_cost / portions_served
        deviation = ((cost_per_portion - self.standard_budget) / self.standard_budget) * 100

        is_plausible = abs(deviation) <= self.tolerance_percent

        flag = None
        if deviation > self.tolerance_percent:
            flag = f"Cost per portion (Rp {cost_per_portion:,.0f}) exceeds budget by {deviation:.1f}%"
        elif deviation < -self.tolerance_percent:
            flag = f"Cost per portion (Rp {cost_per_portion:,.0f}) is {abs(deviation):.1f}% below budget — possible quality concern"

        return {
            "cost_per_portion": round(cost_per_portion, 2),
            "standard_budget": self.standard_budget,
            "deviation_percent": round(deviation, 2),
            "is_plausible": is_plausible,
            "flag": flag,
        }


# ── Singleton ──
cost_plausibility_analyzer = CostPlausibilityAnalyzer()
