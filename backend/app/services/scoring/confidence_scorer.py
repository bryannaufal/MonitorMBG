"""Confidence scorer — measures data completeness and cross-validation strength."""

from typing import Any


class ConfidenceScorer:
    """
    Computes a confidence score (0–1) indicating how trustworthy
    the overall assessment of a report is, based on data completeness
    and cross-validation signals.
    """

    # Fields that contribute to data completeness
    COMPLETENESS_FIELDS = [
        "has_photos",
        "has_menu_description",
        "has_budget_data",
        "has_portion_count",
        "has_ocr_text",
        "has_nutrition_analysis",
    ]

    # Cross-validation checks
    VALIDATION_CHECKS = [
        "photo_text_match",      # Photo matches menu description
        "no_duplicate_images",   # No perceptual hash duplicates
        "cost_within_budget",    # Cost is plausible
        "nutrition_adequate",    # Nutrition meets standards
    ]

    def compute(
        self,
        completeness: dict[str, bool],
        validations: dict[str, bool],
    ) -> dict[str, Any]:
        """
        Compute confidence score.

        Args:
            completeness: {field: bool} for each data completeness check
            validations: {check: bool} for each cross-validation check

        Returns:
            {"score": float, "completeness_ratio": float, "validation_ratio": float}
        """
        # Completeness score (40% weight)
        complete_count = sum(1 for f in self.COMPLETENESS_FIELDS if completeness.get(f, False))
        completeness_ratio = complete_count / len(self.COMPLETENESS_FIELDS) if self.COMPLETENESS_FIELDS else 0

        # Validation score (60% weight)
        valid_count = sum(1 for c in self.VALIDATION_CHECKS if validations.get(c, False))
        validation_ratio = valid_count / len(self.VALIDATION_CHECKS) if self.VALIDATION_CHECKS else 0

        score = (completeness_ratio * 0.4) + (validation_ratio * 0.6)

        return {
            "score": round(score, 3),
            "completeness_ratio": round(completeness_ratio, 3),
            "validation_ratio": round(validation_ratio, 3),
            "missing_data": [f for f in self.COMPLETENESS_FIELDS if not completeness.get(f, False)],
            "failed_checks": [c for c in self.VALIDATION_CHECKS if not validations.get(c, False)],
        }


# ── Singleton ──
confidence_scorer = ConfidenceScorer()
