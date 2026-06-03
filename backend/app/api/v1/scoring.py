"""Scoring API — Severity, confidence, and cost plausibility endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.scoring import ScoreResponse, ScoreListResponse

router = APIRouter()


@router.get("/report/{report_id}", response_model=ScoreResponse)
async def get_report_scores(
    report_id: int,
    session: AsyncSession = Depends(get_session),
):
    """
    Get computed scores for a specific report.

    Returns severity score, confidence score, and cost plausibility analysis.
    """
    # TODO: Implement via scoring service
    return {}


@router.get("/rankings")
async def get_severity_rankings(
    limit: int = Query(20, ge=1, le=100),
    severity: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Get reports ranked by severity score (highest first).

    Used for triage prioritization by operators.
    """
    # TODO: Implement severity-ranked listing
    return {"items": [], "total": 0}


@router.post("/recompute/{report_id}")
async def recompute_scores(
    report_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Trigger a re-computation of all scores for a report."""
    # TODO: Dispatch scoring task via Celery
    return {"message": "Score recomputation dispatched", "report_id": report_id}
