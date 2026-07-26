"""Unified risk scorer — severity + trust + actionability (+ optional bonus).

All inputs are derived from signal fields (rules/keywords), not operator input.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app import seed_data as sd
from app.runtime_store import all_signals

logger = logging.getLogger(__name__)

UNKNOWN = "Belum teridentifikasi"

URGENCY_BASE = {"Kritis": 85, "Tinggi": 70, "Sedang": 50, "Rendah": 30}

SOURCE_TRUST = {
    "Laporan Pengawas": 0.90,
    "Operator Sekolah": 0.80,
    "Formulir Publik": 0.70,
    "Aduan Wali Murid": 0.65,
    "Media Sosial": 0.35,
}

HIGH_RISK_KEYWORDS = (
    "belatung", "keracunan", "kontaminasi", "bacillus", "busuk", "basi",
    "keracunan makanan", "keamanan pangan", "higen", "hygiene",
)
NUTRITION_KEYWORDS = ("protein", "gizi", "porsi", "nutrisi", "menu")
COST_KEYWORDS = ("biaya", "anggaran", "mahal", "markup")

LABEL_THRESHOLDS = ((80, "Kritis"), (65, "Tinggi"), (45, "Sedang"), (0, "Rendah"))


def _text_blob(signal: dict[str, Any]) -> str:
    parts = [
        signal.get("summary") or "",
        signal.get("text") or "",
        signal.get("issue_category") or "",
    ]
    return " ".join(parts).lower()


def _score_severity(signal: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    urgency = signal.get("urgency") or "Sedang"
    base = URGENCY_BASE.get(urgency, 50)
    reasons.append(f"Urgensi sinyal: {urgency}")

    blob = _text_blob(signal)
    score = base
    if any(kw in blob for kw in HIGH_RISK_KEYWORDS):
        score = min(95, score + 15)
        reasons.append("Isu keamanan pangan / kontaminasi terdeteksi pada teks")
    elif any(kw in blob for kw in NUTRITION_KEYWORDS):
        score = min(90, score + 8)
        reasons.append("Isu gizi/porsi terdeteksi pada teks")
    elif any(kw in blob for kw in COST_KEYWORDS):
        score = min(88, score + 6)
        reasons.append("Isu biaya/anggaran terdeteksi pada teks")

    category = (signal.get("issue_category") or "").lower()
    if "keamanan pangan" in category or "keracunan" in category:
        score = min(95, max(score, 75))
        reasons.append("Kategori isu berisiko tinggi")

    return int(score), reasons


def _score_trust(signal: dict[str, Any]) -> tuple[int, list[str]]:
    source = signal.get("source") or "Media Sosial"
    tier = SOURCE_TRUST.get(source, 0.40)
    raw_conf = float(signal.get("source_confidence") or tier)
    trust = min(100, max(5, int(raw_conf * tier * 100)))
    return trust, [f"Sumber: {source} (tingkat kepercayaan channel)"]


def _filled(value: str | None) -> bool:
    v = (value or "").strip()
    return bool(v and v != UNKNOWN)


def _score_actionability(signal: dict[str, Any]) -> tuple[int, list[str]]:
    checks = [
        ("wilayah", _filled(signal.get("region"))),
        ("sekolah/lokasi", _filled(signal.get("school"))),
    ]
    score = int(round(sum(1 for _, ok in checks if ok) / len(checks) * 100))
    reasons = [f"{'✓' if ok else '–'} {label}" for label, ok in checks]
    if signal.get("attachment_path"):
        score = min(100, score + 15)
        reasons.append("✓ lampiran (+15 dapat ditindak)")
    else:
        reasons.append("– lampiran")
    if _filled(signal.get("district")):
        score = min(100, score + 10)
        reasons.append("✓ kabupaten/kota teridentifikasi")
    return min(100, score), reasons


def _bonus(signal: dict[str, Any]) -> tuple[int, list[str]]:
    bonus = 0
    reasons: list[str] = []
    vendor_id = signal.get("vendor_id")
    if vendor_id and vendor_id in sd.VENDOR_BY_ID:
        vendor = sd.VENDOR_BY_ID[vendor_id]
        if vendor.get("watchlist") or vendor.get("risk_score", 0) >= 75:
            bonus += 8
            reasons.append("Vendor pada watchlist / riwayat risiko")

    # Corroboration: another unlinked signal with similar keywords in same region
    blob = _text_blob(signal)
    region = signal.get("region")
    if region and region != UNKNOWN:
        for other in all_signals():
            if other["id"] == signal.get("id"):
                continue
            if other.get("region") == region and _text_overlap(blob, _text_blob(other)):
                bonus += 5
                reasons.append("Ada sinyal serupa di wilayah yang sama")
                break

    return bonus, reasons


def _text_overlap(a: str, b: str) -> bool:
    words_a = {w for w in re.split(r"\W+", a) if len(w) > 3}
    words_b = {w for w in re.split(r"\W+", b) if len(w) > 3}
    return len(words_a & words_b) >= 2


def _label(score: int) -> str:
    for threshold, label in LABEL_THRESHOLDS:
        if score >= threshold:
            return label
    return "Rendah"


def _score_signal_rules(signal: dict[str, Any]) -> tuple[int, list[str], int, list[str]]:
    severity, sev_reasons = _score_severity(signal)
    actionability, act_reasons = _score_actionability(signal)
    return severity, sev_reasons, actionability, act_reasons


def _assemble_result(
    signal: dict[str, Any],
    *,
    severity: int,
    sev_reasons: list[str],
    trust: int,
    trust_reasons: list[str],
    actionability: int,
    act_reasons: list[str],
    bonus: int,
    bonus_reasons: list[str],
    scoring_engine: str,
    nutrition_score: int | None = None,
    nutrition_reasons: list[str] | None = None,
    nutrition_engine: str = "none",
) -> dict[str, Any]:
    final = min(
        95,
        int(severity * 0.50 + trust * 0.25 + actionability * 0.25) + bonus,
    )
    label = _label(final)

    reasons = [
        f"Dampak isu: {severity}/100 — {'; '.join(sev_reasons[:2])}",
        f"Kepercayaan sumber: {trust}/100 — {trust_reasons[0]}",
        f"Dapat ditindak: {actionability}/100 — {'; '.join(act_reasons[:2])}",
    ]
    if bonus_reasons:
        reasons.append(f"Bonus pola: +{bonus} — {'; '.join(bonus_reasons)}")
    if nutrition_score is not None:
        src = "Kimi vision" if nutrition_engine == "kimi_vision" else "estimasi deskripsi + lampiran"
        reasons.append(
            f"Gizi: {nutrition_score}/100 ({src}) — "
            f"{'; '.join((nutrition_reasons or [])[:2])}"
        )

    if scoring_engine == "kimi":
        explanation = (
            "Penilaian pra-verifikasi: dampak isu dan kesiapan tindak dari Kimi; "
            "kepercayaan sumber dan bonus pola tetap berbasis aturan channel. "
        )
    else:
        explanation = (
            "Penilaian otomatis (pra-verifikasi) dari urgensi isu, kepercayaan sumber, "
            "dan kelengkapan data. "
        )
    if nutrition_score is not None:
        if nutrition_engine == "kimi_vision":
            explanation += "Gizi diestimasi dari foto (Kimi vision). "
        else:
            explanation += "Gizi diestimasi dari deskripsi isu dan keberadaan lampiran. "
    explanation += "Bukan keputusan final — operator dapat menyesuaikan."

    return {
        "severity_score": severity,
        "confidence_score": trust,
        "actionability_score": actionability,
        "nutrition_score": nutrition_score,
        "final_priority_score": final,
        "priority_label": label,
        "priority_mode": "suggested",
        "scoring_engine": scoring_engine,
        "reasons": reasons,
        "explanation": explanation,
        "recommended_action": (
            "Jadwalkan verifikasi lapangan segera."
            if final >= 65
            else "Kumpulkan bukti tambahan dan klarifikasi lokasi/vendor."
            if final >= 45
            else "Pantau sinyal; prioritaskan jika ada sinyal pendukung."
        ),
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }


def _llm_scoring_enabled() -> bool:
    """Kimi hanya dipanggil saat SCRAPER_MODE=live. Fixture = rules + seed demo."""
    from app.config import settings

    if (settings.SCRAPER_MODE or "").lower() == "fixture":
        return False
    return bool((settings.KIMI_API_KEY or "").strip())


def score_signal(signal: dict[str, Any]) -> dict[str, Any]:
    """Compute suggested risk assessment for a signal.

    Seed signals (id 1–20): pre-baked assessment — never calls Kimi.
    SCRAPER_MODE=fixture: rules-only for runtime signals.
    SCRAPER_MODE=live + KIMI_API_KEY: Kimi for runtime signals only.
    """
    from app.services.scoring.seed_signal_assessment import get_seed_signal_assessment, is_seed_signal

    if is_seed_signal(signal):
        baked = get_seed_signal_assessment(int(signal["id"]))
        if baked:
            return baked

    from app.services.scoring.nutrition_scorer import score_nutrition

    trust, trust_reasons = _score_trust(signal)
    bonus, bonus_reasons = _bonus(signal)
    nutrition_score, nutrition_reasons, nutrition_engine = score_nutrition(signal)

    kimi = None
    if _llm_scoring_enabled():
        from app.services.scoring.kimi_signal_scorer import score_signal_with_kimi

        kimi = score_signal_with_kimi(signal)

    if kimi:
        return _assemble_result(
            signal,
            severity=kimi["severity_score"],
            sev_reasons=kimi["severity_reasons"],
            trust=trust,
            trust_reasons=trust_reasons,
            actionability=kimi["actionability_score"],
            act_reasons=kimi["actionability_reasons"],
            bonus=bonus,
            bonus_reasons=bonus_reasons,
            scoring_engine="kimi",
            nutrition_score=nutrition_score,
            nutrition_reasons=nutrition_reasons,
            nutrition_engine=nutrition_engine,
        )

    logger.info(
        "Kimi skipped/failed for signal #%s - using rules fallback",
        signal.get("id", "?"),
    )
    severity, sev_reasons, actionability, act_reasons = _score_signal_rules(signal)
    return _assemble_result(
        signal,
        severity=severity,
        sev_reasons=sev_reasons,
        trust=trust,
        trust_reasons=trust_reasons,
        actionability=actionability,
        act_reasons=act_reasons,
        bonus=bonus,
        bonus_reasons=bonus_reasons,
        scoring_engine="rules",
        nutrition_score=nutrition_score,
        nutrition_reasons=nutrition_reasons,
        nutrition_engine=nutrition_engine,
    )
