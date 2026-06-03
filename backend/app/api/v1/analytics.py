"""Analytics API — Aggregated data for dashboard visualizations."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    session: AsyncSession = Depends(get_session),
):
    """
    Get dashboard overview stats.

    Returns total complaints, reports, verification rates,
    average severity, and trend indicators.
    """
    # TODO: Aggregate from all data sources
    return {
        "total_complaints": 0,
        "total_reports": 0,
        "total_daily_reports": 0,
        "verification_rate": 0.0,
        "avg_severity_score": 0.0,
        "flagged_reports": 0,
    }


@router.get("/heatmap")
async def get_issue_heatmap(
    date_from: str | None = None,
    date_to: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    """
    Get geographic heatmap data for issue distribution.

    Returns complaint/report counts aggregated by region.
    """
    # TODO: Aggregate complaint locations by region
    return {"regions": []}


@router.get("/trends")
async def get_trend_data(
    metric: str = Query("complaints", description="Metric to trend: complaints, severity, nutrition"),
    period: str = Query("7d", description="Time period: 7d, 30d, 90d"),
    session: AsyncSession = Depends(get_session),
):
    """
    Get time-series trend data for dashboard charts.
    """
    # TODO: Compute time-series aggregations
    return {"metric": metric, "period": period, "data_points": []}


@router.get("/anomalies")
async def get_detected_anomalies(
    session: AsyncSession = Depends(get_session),
):
    """
    Get recently detected anomalies/spikes in complaint data.
    """
    # TODO: Return anomalies from NLP engine
    return {"anomalies": []}
