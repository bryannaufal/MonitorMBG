"""Analytics API — Aggregated demo data for dashboard visualizations."""

from fastapi import APIRouter, Query

from app import demo_data

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview():
    """Get national MonitorMBG command-center KPIs."""
    return demo_data.overview()


@router.get("/heatmap")
async def get_issue_heatmap(
    date_from: str | None = None,
    date_to: str | None = None,
):
    """Get regional risk and complaint distribution."""
    return {"regions": demo_data.REGIONAL_HEATMAP, "date_from": date_from, "date_to": date_to}


@router.get("/trends")
async def get_trend_data(
    metric: str = Query("complaints", description="Metric to trend: complaints, severity, nutrition"),
    period: str = Query("7d", description="Time period: 7d, 30d, 90d"),
):
    """Get demo time-series trend data."""
    return {"metric": metric, "period": period, "data_points": demo_data.TRENDS}


@router.get("/anomalies")
async def get_detected_anomalies():
    """Get deterministic demo anomalies/spikes."""
    return {"anomalies": demo_data.ANOMALIES}
