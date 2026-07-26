"""Nutrition API — Food nutrition estimation result endpoints."""

from fastapi import APIRouter

from app import demo_data

router = APIRouter()


@router.get("/report/{report_id}")
async def get_nutrition_results(report_id: int):
    """
    Get nutrition estimation results for a daily report.

    Returns detected food items, portion estimates, and
    calorie/macronutrient calculations.
    """
    report = demo_data.get_or_404(demo_data.DAILY_REPORTS, report_id, "Daily report")
    score = next((item for item in demo_data.SCORES if item["report_id"] == report_id), None)
    return {
        "report_id": report_id,
        "vendor_id": report["vendor_id"],
        "vendor_name": report["vendor_name"],
        "menu_estimate": report["actual_menu"],
        "planned_menu": report["planned_menu"],
        "nutrition_estimate": report["nutrition_estimate"],
        "portion_adequacy": "Needs Review" if score and score.get("severity_score", 0) >= 70 else "Adequate",
        "nutrition_concern_score": score.get("severity_score", 0) if score else 0,
        "cost_per_portion": report["cost_estimate"]["cost_per_portion"],
        "cost_anomaly_flag": report["cost_estimate"]["cost_anomaly_flag"],
        "recommended_follow_up": report["recommended_follow_up"],
        "ai_notice": demo_data.DEMO_NOTICE,
    }


@router.get("/summary")
async def get_nutrition_summary(
    region: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
):
    """
    Get aggregated nutrition summary across reports.

    Returns average calorie counts, macronutrient distribution,
    and compliance with nutritional standards.
    """
    reports = demo_data.DAILY_REPORTS
    if region:
        reports = [item for item in reports if item["region"].lower() == region.lower()]
    count = max(1, len(reports))
    avg = lambda key: round(sum(item["nutrition_estimate"][key] for item in reports) / count, 1)
    flagged = [item for item in reports if item["cost_estimate"]["cost_anomaly_flag"] or item["mismatch_indicator"]]
    return {
        "avg_calories": avg("calories"),
        "avg_protein_g": avg("protein_g"),
        "avg_carbs_g": avg("carbs_g"),
        "avg_fat_g": avg("fat_g"),
        "total_reports_analyzed": len(reports),
        "flagged_reports": flagged,
        "date_from": date_from,
        "date_to": date_to,
        "ai_notice": demo_data.DEMO_NOTICE,
    }
