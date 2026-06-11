"""Scoring API — Severity, confidence, and cost plausibility endpoints."""

from fastapi import APIRouter, Query

from app import demo_data

router = APIRouter()


@router.get("/report/{report_id}")
async def get_report_scores(report_id: int):
    """
    Get computed scores for a specific report.

    Returns severity score, confidence score, and cost plausibility analysis.
    """
    score = next((item for item in demo_data.SCORES if item["report_id"] == report_id), None)
    if score is None:
        return demo_data.get_or_404([], report_id, "Score")
    return score


@router.get("/rankings")
async def get_severity_rankings(
    limit: int = Query(20, ge=1, le=100),
    severity: str | None = None,
):
    """
    Get reports ranked by severity score (highest first).

    Used for triage prioritization by operators.
    """
    items = sorted(demo_data.SCORES, key=lambda item: item["final_priority_score"], reverse=True)
    if severity:
        items = [item for item in items if item["priority_label"].lower() == severity.lower()]
    return {"items": items[:limit], "total": len(items)}


@router.post("/recompute/{report_id}")
async def recompute_scores(
    report_id: int,
):
    """Trigger a re-computation of all scores for a report."""
    score = next((item for item in demo_data.SCORES if item["report_id"] == report_id), None)
    if score is None:
        demo_data.get_or_404([], report_id, "Score")
    return {
        "message": "Demo score recomputed deterministically.",
        "report_id": report_id,
        "score": score,
        "ai_notice": demo_data.DEMO_NOTICE,
    }
