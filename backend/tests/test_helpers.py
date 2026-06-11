from app.services.cv_engine.nutrition_calculator import nutrition_calculator
from app.services.scoring.severity_scorer import severity_scorer


def test_nutrition_calculator_known_food():
    result = nutrition_calculator.calculate_item("rice", 200)
    assert result["calories"] == 260
    assert result["carbs_g"] == 56


def test_severity_scorer_explainable_output():
    result = severity_scorer.compute(
        {
            "sentiment": 1.0,
            "frequency": 0.8,
            "verification": 0.9,
            "cost_anomaly": 0.7,
            "nutrition_gap": 0.6,
            "duplicate_flag": 1.0,
        }
    )
    assert result["score"] > 70
    assert result["level"] in {"high", "critical"}
    assert "sentiment" in result["breakdown"]
