"""Severity scorer — computes multi-signal severity scores for reports."""

from typing import Any

from app.utils.constants import SeverityLevel


class SeverityScorer:
    """
    Computes a severity score (0–100) for a report by combining
    multiple signals: NLP sentiment, complaint frequency, CV verification
    flags, and cost anomalies.
    """

    # Weight configuration for each signal
    WEIGHTS = {
        "sentiment": 0.20,
        "frequency": 0.15,
        "verification": 0.25,
        "cost_anomaly": 0.20,
        "nutrition_gap": 0.10,
        "duplicate_flag": 0.10,
    }

    def compute(self, signals: dict[str, float]) -> dict[str, Any]:
        """
        Compute a weighted severity score from input signals.

        Args:
            signals: {
                "sentiment": float (0-1, where 1 = very negative),
                "frequency": float (0-1, normalized complaint frequency),
                "verification": float (0-1, where 1 = failed verification),
                "cost_anomaly": float (0-1, deviation from budget),
                "nutrition_gap": float (0-1, deviation from nutrition standards),
                "duplicate_flag": float (0 or 1, duplicate image detected),
            }

        Returns:
            {"score": float, "level": SeverityLevel, "breakdown": dict}
        """
        weighted_sum = 0.0
        breakdown = {}

        for signal, weight in self.WEIGHTS.items():
            value = signals.get(signal, 0.0)
            contribution = value * weight * 100
            weighted_sum += contribution
            breakdown[signal] = {
                "value": round(value, 3),
                "weight": weight,
                "contribution": round(contribution, 2),
            }

        score = round(min(weighted_sum, 100.0), 2)
        level = self._score_to_level(score)

        return {
            "score": score,
            "level": level.value,
            "breakdown": breakdown,
        }

    @staticmethod
    def _score_to_level(score: float) -> SeverityLevel:
        """Map a numeric score to a severity level."""
        if score >= 75:
            return SeverityLevel.CRITICAL
        elif score >= 50:
            return SeverityLevel.HIGH
        elif score >= 25:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW


# ── Singleton ──
severity_scorer = SeverityScorer()
