"""Time-series anomaly detection for complaint volume spikes."""

from datetime import datetime
from typing import Any


class AnomalyDetector:
    """
    Detects anomalous spikes in time-series complaint data.

    Uses statistical methods (Z-score, moving average deviation)
    to identify unusual increases in complaint volumes.
    """

    def __init__(self, z_threshold: float = 2.5, window_size: int = 7):
        self.z_threshold = z_threshold
        self.window_size = window_size

    def detect_spikes(
        self,
        timestamps: list[datetime],
        values: list[float],
    ) -> list[dict[str, Any]]:
        """
        Detect anomalous spikes in a time-series.

        Args:
            timestamps: List of datetime points
            values: Corresponding complaint counts or metric values

        Returns:
            List of detected anomalies with timestamp, value, and z-score
        """
        if len(values) < self.window_size + 1:
            return []

        arr = [float(value) for value in values]
        anomalies = []

        for i in range(self.window_size, len(arr)):
            window = arr[i - self.window_size : i]
            mean = sum(window) / len(window)
            variance = sum((value - mean) ** 2 for value in window) / len(window)
            std = variance ** 0.5

            if std == 0:
                continue

            z_score = (arr[i] - mean) / std

            if abs(z_score) > self.z_threshold:
                anomalies.append({
                    "timestamp": timestamps[i].isoformat(),
                    "value": float(arr[i]),
                    "z_score": float(z_score),
                    "window_mean": float(mean),
                    "is_spike": z_score > 0,
                })

        return anomalies

    def detect_trend_change(
        self,
        values: list[float],
        lookback: int = 14,
    ) -> dict[str, Any]:
        """
        Detect if there's a significant trend change (increasing/decreasing).

        Returns:
            {"trend": "increasing"|"decreasing"|"stable", "slope": float}
        """
        if len(values) < lookback:
            return {"trend": "stable", "slope": 0.0}

        recent = [float(value) for value in values[-lookback:]]
        n = len(recent)
        x_values = list(range(n))
        x_mean = sum(x_values) / n
        y_mean = sum(recent) / n
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        slope = (
            sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, recent)) / denominator
            if denominator
            else 0.0
        )

        if slope > 0.5:
            trend = "increasing"
        elif slope < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"

        return {"trend": trend, "slope": float(slope)}


# ── Singleton ──
anomaly_detector = AnomalyDetector()
