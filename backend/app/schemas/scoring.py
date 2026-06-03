"""Scoring schemas — request/response DTOs for the hybrid scoring engine."""

from pydantic import BaseModel

from app.utils.constants import SeverityLevel


class CostPlausibility(BaseModel):
    """Cost plausibility analysis result."""
    cost_per_portion: float | None = None
    standard_budget: float | None = None
    deviation_percent: float | None = None
    is_plausible: bool | None = None
    notes: str | None = None


class ScoreResponse(BaseModel):
    """Complete scoring result for a report."""
    report_id: int | None = None
    severity_score: float | None = None
    severity_level: SeverityLevel | None = None
    confidence_score: float | None = None
    cost_plausibility: CostPlausibility | None = None
    contributing_factors: list[str] = []
    computed_at: str | None = None


class ScoreListResponse(BaseModel):
    """Paginated list of scored reports."""
    items: list[ScoreResponse] = []
    total: int = 0
