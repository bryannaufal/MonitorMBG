"""Tests for nutrition (GIZI) scoring."""

from app.services.scoring.nutrition_scorer import score_nutrition, score_nutrition_rules


def test_no_attachment_returns_none():
    score, reasons, engine = score_nutrition({"summary": "tes gizi", "text": "protein rendah"})
    assert score is None
    assert engine == "none"
    assert reasons == []


def test_rules_lowers_score_for_contamination_keywords():
    signal = {
        "attachment_path": "/evidence-media/4.jpg",
        "summary": "Dugaan belatung pada porsi MBG",
        "text": "Warga laporkan kontaminasi dan protein rendah",
        "issue_category": "dugaan keamanan pangan",
    }
    score, reasons = score_nutrition_rules(signal)
    assert score < 68
    assert any("belatung" in r for r in reasons)


def test_rules_raises_score_for_positive_keywords():
    signal = {
        "attachment_path": "/evidence-media/8.jpg",
        "summary": "Menu lengkap dengan sayur dan protein",
        "text": "Porsi cukup dan gizi baik",
        "issue_category": "umum",
    }
    score, _ = score_nutrition_rules(signal)
    assert score >= 68


def test_fixture_mode_uses_rules_with_attachment():
    from unittest.mock import patch

    signal = {
        "attachment_path": "/evidence-media/4.jpg",
        "summary": "Dugaan belatung",
        "text": "kontaminasi",
    }
    with patch("app.services.scoring.nutrition_scorer.settings") as mock_settings:
        mock_settings.SCRAPER_MODE = "fixture"
        mock_settings.KIMI_API_KEY = "sk-test"
        score, _, engine = score_nutrition(signal)
    assert engine == "rules"
    assert score is not None
