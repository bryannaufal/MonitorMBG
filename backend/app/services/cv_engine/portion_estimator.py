"""Portion size estimator from food detection bounding boxes."""

from typing import Any
import math


class PortionEstimator:
    """
    Estimates food portion sizes from bounding box areas.

    Uses reference-based scaling: given a known plate size,
    estimates the volume/weight of detected food items based
    on their relative area on the plate.
    """

    # Average plate diameter in cm and typical plate area
    PLATE_DIAMETER_CM = 25.0
    PLATE_AREA_CM2 = math.pi * (25.0 / 2) ** 2

    # Average food density assumptions (g/cm³ for plated food)
    DENSITY_MAP: dict[str, float] = {
        "rice": 1.1,
        "chicken": 0.9,
        "fish": 0.85,
        "egg": 1.05,
        "tempe": 0.8,
        "tofu": 0.7,
        "vegetable": 0.4,
        "fruit": 0.6,
        "default": 0.8,
    }

    # Assumed average food height on plate (cm)
    AVERAGE_HEIGHT_CM = 2.0

    def estimate_portion(
        self,
        food_name: str,
        bbox: dict[str, float],
        plate_bbox: dict[str, float] | None = None,
    ) -> float:
        """
        Estimate portion size in grams from bounding box.

        Args:
            food_name: Name of the detected food
            bbox: {"x": float, "y": float, "width": float, "height": float} in pixels
            plate_bbox: Optional plate bounding box for reference scaling

        Returns:
            Estimated portion size in grams
        """
        # Calculate item area in pixels
        item_area_px = bbox["width"] * bbox["height"]

        if plate_bbox:
            plate_area_px = plate_bbox["width"] * plate_bbox["height"]
            area_ratio = item_area_px / plate_area_px if plate_area_px > 0 else 0.1
        else:
            # Assume food takes ~25% of a typical frame
            area_ratio = 0.25

        # Convert to physical area
        area_cm2 = area_ratio * self.PLATE_AREA_CM2

        # Estimate volume (area × assumed height)
        volume_cm3 = area_cm2 * self.AVERAGE_HEIGHT_CM

        # Convert to weight using density
        density = self.DENSITY_MAP.get(food_name.lower(), self.DENSITY_MAP["default"])
        weight_grams = volume_cm3 * density

        return round(weight_grams, 1)

    def estimate_plate(
        self,
        detections: list[dict[str, Any]],
        plate_bbox: dict[str, float] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Estimate portions for all detected items on a plate.

        Args:
            detections: List of {"name": str, "bounding_box": dict}

        Returns:
            List of {"name": str, "portion_grams": float}
        """
        results = []
        for det in detections:
            portion = self.estimate_portion(
                det["name"],
                det.get("bounding_box", {"x": 0, "y": 0, "width": 100, "height": 100}),
                plate_bbox,
            )
            results.append({
                "name": det["name"],
                "portion_grams": portion,
                "confidence": det.get("confidence", 0.0),
            })
        return results


# ── Singleton ──
portion_estimator = PortionEstimator()
