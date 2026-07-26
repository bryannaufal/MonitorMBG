"""Auto-ticket eligibility gate based on risk score."""

from __future__ import annotations

from typing import Any

UNKNOWN = "Belum teridentifikasi"
HIGH_RISK_CATEGORIES = {
    "dugaan keamanan pangan",
    "indikasi keracunan makanan",
    "kekhawatiran higiene",
}


def _is_social(signal: dict[str, Any]) -> bool:
    return "sosial" in (signal.get("source") or "").lower()


def _location_incomplete(signal: dict[str, Any]) -> bool:
    region = signal.get("region") or UNKNOWN
    school = signal.get("school") or UNKNOWN
    return region == UNKNOWN or school == UNKNOWN


def evaluate(signal: dict[str, Any], risk: dict[str, Any]) -> tuple[bool, str]:
    score = int(risk.get("final_priority_score") or 0)
    severity = int(risk.get("severity_score") or 0)

    if score < 55:
        return False, "Skor prioritas di bawah ambang auto-ticket (55)"

    triggers: list[str] = []
    if (signal.get("urgency") or "") == "Kritis":
        triggers.append("urgensi kritis")
    if (signal.get("issue_category") or "") in HIGH_RISK_CATEGORIES:
        triggers.append("kategori isu berisiko tinggi")
    if signal.get("attachment_path"):
        triggers.append("ada lampiran")
    if severity >= 75:
        triggers.append("dampak isu tinggi")

    if not triggers:
        return False, "Skor cukup tetapi tidak ada trigger risiko (urgensi/lampiran/kategori)"

    if _is_social(signal) and _location_incomplete(signal) and score < 75:
        return False, "Sinyal media sosial minim data — butuh skor ≥ 75 untuk auto-ticket"

    return True, f"Lolos gate: {', '.join(triggers)} (skor {score})"
