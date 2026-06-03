"""Scoring Celery tasks — severity, confidence, and cost plausibility."""

from app.workers.celery_app import celery_app


@celery_app.task(name="scoring.compute_scores", bind=True)
def compute_scores(self, report_id: int, report_type: str):
    """
    Compute all scores (severity, confidence, cost plausibility) for a report.

    Args:
        report_id: ID of the report to score
        report_type: "official" or "daily"
    """
    from app.services.scoring.severity_scorer import severity_scorer
    from app.services.scoring.confidence_scorer import confidence_scorer
    from app.services.scoring.cost_plausibility import cost_plausibility_analyzer

    # TODO: Fetch report data and related signals from DB
    # For now, using placeholder signals

    # Severity scoring
    severity_signals = {
        "sentiment": 0.0,
        "frequency": 0.0,
        "verification": 0.0,
        "cost_anomaly": 0.0,
        "nutrition_gap": 0.0,
        "duplicate_flag": 0.0,
    }
    severity_result = severity_scorer.compute(severity_signals)

    # Confidence scoring
    completeness = {
        "has_photos": False,
        "has_menu_description": False,
        "has_budget_data": False,
        "has_portion_count": False,
        "has_ocr_text": False,
        "has_nutrition_analysis": False,
    }
    validations = {
        "photo_text_match": False,
        "no_duplicate_images": True,
        "cost_within_budget": False,
        "nutrition_adequate": False,
    }
    confidence_result = confidence_scorer.compute(completeness, validations)

    # Cost plausibility (if budget data available)
    # TODO: Fetch actual cost and portions from DB
    # cost_result = cost_plausibility_analyzer.analyze(total_cost, portions)

    # TODO: Store score results in the database
    return {
        "report_id": report_id,
        "report_type": report_type,
        "severity": severity_result,
        "confidence": confidence_result,
    }
