"""Application-wide constants, enums, and reference data."""

from enum import Enum


# ── Complaint / Signal Enums ──

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ComplaintSource(str, Enum):
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    NEWS = "news"
    OTHER = "other"


class ComplaintStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# ── Report Enums ──

class ReportType(str, Enum):
    OFFICIAL = "official"
    DAILY = "daily"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FLAGGED = "flagged"
    REJECTED = "rejected"


# ── Severity Levels ──

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Standard Budget Reference (IDR per portion) ──
# Used by the Cost Plausibility Engine
STANDARD_BUDGET_PER_PORTION_IDR = 15_000
BUDGET_TOLERANCE_PERCENT = 20  # ±20% threshold

# ── Perceptual Hashing Thresholds ──
PHASH_DUPLICATE_THRESHOLD = 8       # Hamming distance ≤ 8 = likely duplicate
PHASH_SIMILAR_THRESHOLD = 16        # Hamming distance ≤ 16 = visually similar

# ── Nutrition Reference (per 100g, approximate) ──
# This would typically come from a database; these are starter defaults
DEFAULT_NUTRITION_DB = {
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28.0, "fat": 0.3},
    "chicken": {"calories": 239, "protein": 27.3, "carbs": 0.0, "fat": 13.6},
    "egg": {"calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0},
    "tempe": {"calories": 192, "protein": 18.5, "carbs": 9.4, "fat": 10.8},
    "tofu": {"calories": 76, "protein": 8.0, "carbs": 1.9, "fat": 4.8},
    "vegetable": {"calories": 25, "protein": 1.5, "carbs": 5.0, "fat": 0.2},
    "fish": {"calories": 206, "protein": 22.0, "carbs": 0.0, "fat": 12.0},
    "fruit": {"calories": 52, "protein": 0.3, "carbs": 14.0, "fat": 0.2},
}
