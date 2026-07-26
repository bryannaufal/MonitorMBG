"""Tests for Kimi signal scoring integration."""

from unittest.mock import patch

from app.services.intake.normalizer import from_public_form
from app.services.scoring.kimi_signal_scorer import score_signal_with_kimi
from app.services.scoring.risk_scorer import score_signal


def test_score_signal_rules_when_no_kimi_key():
    signal = from_public_form({
        "description": "Dugaan kontaminasi belatung pada makanan MBG.",
        "region": "Lampung",
        "school": "SDN 1 Karang Agung",
        "issue_category": "dugaan keamanan pangan",
    })
    with patch("app.services.scoring.kimi_signal_scorer.settings") as mock_settings:
        mock_settings.KIMI_API_KEY = ""
        mock_settings.KIMI_BASE_URL = "https://api.moonshot.ai/v1"
        mock_settings.KIMI_MODEL = "moonshot-v1-8k"
        mock_settings.KIMI_TIMEOUT_SECONDS = 60.0
        result = score_signal(signal)
    assert result["scoring_engine"] == "rules"
    assert 0 <= result["severity_score"] <= 100
    assert 0 <= result["actionability_score"] <= 100


def test_score_signal_uses_kimi_when_available():
    signal = from_public_form({
        "description": "Laporan tidak jelas tentang makan siang.",
        "region": "Jawa Barat",
        "school": "SDN 1",
    })
    kimi_out = {
        "severity_score": 82,
        "actionability_score": 71,
        "severity_reasons": ["Isu keamanan pangan implisit"],
        "actionability_reasons": ["Lokasi sekolah disebutkan"],
    }
    with patch("app.services.scoring.risk_scorer._llm_scoring_enabled", return_value=True), patch(
        "app.services.scoring.kimi_signal_scorer.score_signal_with_kimi",
        return_value=kimi_out,
    ):
        result = score_signal(signal)
    assert result["scoring_engine"] == "kimi"
    assert result["severity_score"] == 82
    assert result["actionability_score"] == 71
    assert result["confidence_score"] > 0


def test_seed_signal_skips_kimi_even_in_live_mode():
    signal = {"id": 19, "summary": "belatung", "text": "test", "urgency": "Kritis"}
    with patch("app.services.scoring.risk_scorer._llm_scoring_enabled", return_value=True), patch(
        "app.services.scoring.kimi_signal_scorer.score_signal_with_kimi",
    ) as mock_kimi, patch(
        "app.services.scoring.nutrition_scorer.score_nutrition_with_kimi",
    ) as mock_nutrition:
        result = score_signal(signal)
        mock_kimi.assert_not_called()
        mock_nutrition.assert_not_called()
    assert result["scoring_engine"] == "seed"
    assert result["nutrition_score"] == 28
    gizi_lines = [r for r in result.get("reasons") or [] if r.startswith("Gizi:")]
    assert len(gizi_lines) == 1


def test_score_signal_fixture_skips_kimi():
    signal = from_public_form({
        "description": "Laporan dengan foto.",
        "region": "Jawa Barat",
        "school": "SDN 1",
    })
    with patch("app.services.scoring.risk_scorer._llm_scoring_enabled", return_value=False), patch(
        "app.services.scoring.kimi_signal_scorer.score_signal_with_kimi",
    ) as mock_kimi:
        result = score_signal(signal)
        mock_kimi.assert_not_called()
    assert result["scoring_engine"] == "rules"


def test_kimi_scorer_returns_none_without_key():
    signal = {"summary": "test", "text": "test"}
    with patch("app.services.scoring.kimi_signal_scorer.settings") as mock_settings:
        mock_settings.KIMI_API_KEY = ""
        assert score_signal_with_kimi(signal) is None
