"""Tests for unified risk scorer and auto-ticket gate."""

from app.runtime_store import RUNTIME_SIGNALS, append_signal
from app.services.intake.normalizer import from_public_form, from_social_raw
from app.services.scoring.risk_scorer import score_signal
from app.services.ticketing import auto_ticket_gate


def test_form_signal_scores_higher_than_vague_social():
    form = from_public_form({
        "description": "Dugaan kontaminasi belatung pada makanan MBG di SDN 1 Karang Agung, Lampung.",
        "region": "Lampung",
        "school": "SDN 1 Karang Agung",
        "issue_category": "dugaan keamanan pangan",
    })
    social = from_social_raw({
        "text": "mbg enak",
        "summary": "mbg enak",
        "region": "Belum teridentifikasi",
    }, intake_origin="scraper_fixture")
    form_score = score_signal(form)["final_priority_score"]
    social_score = score_signal(social)["final_priority_score"]
    assert form_score > social_score


def test_auto_ticket_gate_blocks_low_social():
    signal = from_social_raw({
        "text": "mbg enak di sekolah",
        "summary": "mbg enak",
    }, intake_origin="scraper_fixture")
    risk = score_signal(signal)
    eligible, _ = auto_ticket_gate.evaluate(signal, risk)
    assert eligible is False


def test_runtime_signals_append_only():
    before = len(RUNTIME_SIGNALS)
    append_signal(from_social_raw({"text": "unique test signal xyz123", "summary": "unique test"}, intake_origin="scraper_fixture"))
    assert len(RUNTIME_SIGNALS) == before + 1


def test_photo_adds_15_actionability():
    base = {
        "description": "Dugaan kontaminasi belatung",
        "region": "Lampung",
        "issue_category": "dugaan keamanan pangan",
    }
    without = score_signal(from_public_form(base))
    with_photo = score_signal(from_public_form({**base, "attachment_path": "/evidence-media/4.jpg"}))
    assert with_photo["actionability_score"] - without["actionability_score"] == 15
    assert with_photo["actionability_score"] <= 100
