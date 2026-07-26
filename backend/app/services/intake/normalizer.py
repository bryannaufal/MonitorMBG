"""Normalize raw intake (form, scrape) into canonical Signal dicts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import seed_data as sd
from app.runtime_store import next_signal_id

UNKNOWN = "Belum teridentifikasi"
EVIDENCE_MEDIA_BASE = sd.EVIDENCE_MEDIA_BASE

HIGH_RISK = ("belatung", "keracunan", "kontaminasi", "busuk", "basi")
NUTRITION = ("protein", "porsi", "gizi", "nutrisi")
COST = ("biaya", "anggaran", "mahal")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _infer_urgency(text: str, issue_category: str) -> str:
    blob = f"{text} {issue_category}".lower()
    if any(k in blob for k in HIGH_RISK):
        return "Kritis"
    if any(k in blob for k in NUTRITION + COST):
        return "Tinggi"
    return "Sedang"


def _infer_category(text: str, explicit: str | None = None) -> str:
    if explicit and explicit.strip() and explicit != UNKNOWN:
        return explicit.strip()
    blob = text.lower()
    if any(k in blob for k in HIGH_RISK):
        return "dugaan keamanan pangan"
    if any(k in blob for k in NUTRITION):
        return "porsi protein kurang"
    if any(k in blob for k in COST):
        return "anomali biaya"
    return "belum diklasifikasi"


def _summary(text: str, max_len: int = 120) -> str:
    clean = " ".join((text or "").split())
    if len(clean) <= max_len:
        return clean or "Laporan MBG masuk"
    return clean[: max_len - 1] + "…"


def from_public_form(payload: dict[str, Any]) -> dict[str, Any]:
    description = (payload.get("description") or "").strip()
    issue = _infer_category(description, payload.get("issue_category"))
    region = (payload.get("region") or UNKNOWN).strip() or UNKNOWN
    district = (payload.get("district") or UNKNOWN).strip() or UNKNOWN
    school = (payload.get("school") or UNKNOWN).strip() or UNKNOWN
    signal: dict[str, Any] = {
        "id": next_signal_id(),
        "case_id": None,
        "source": "Formulir Publik",
        "source_confidence": 0.70,
        "urgency": _infer_urgency(description, issue),
        "status": "Belum Dibentuk Kasus",
        "summary": _summary(description),
        "text": description,
        "vendor_id": None,
        "vendor_name": UNKNOWN,
        "region": region,
        "district": district,
        "school": school,
        "issue_category": issue,
        "created_at": _now(),
        "intake_origin": "public_form",
    }
    if payload.get("attachment_path"):
        signal["attachment_path"] = payload["attachment_path"]
        signal["attachment_title"] = payload.get("attachment_title") or "Foto laporan publik"
        signal["attachment_source"] = "Formulir Publik"
    return signal


def from_social_raw(raw: dict[str, Any], *, intake_origin: str) -> dict[str, Any]:
    text = (raw.get("text") or raw.get("summary") or "").strip()
    issue = _infer_category(text)
    region = (raw.get("region") or UNKNOWN).strip() or UNKNOWN
    signal: dict[str, Any] = {
        "id": next_signal_id(),
        "case_id": None,
        "source": "Media Sosial",
        "source_confidence": float(raw.get("source_confidence") or 0.38),
        "urgency": _infer_urgency(text, issue),
        "status": "Belum Dibentuk Kasus",
        "summary": _summary(raw.get("summary") or text),
        "text": text,
        "vendor_id": None,
        "vendor_name": UNKNOWN,
        "region": region,
        "district": raw.get("district") or UNKNOWN,
        "school": raw.get("school") or UNKNOWN,
        "issue_category": issue,
        "created_at": raw.get("created_at") or _now(),
        "intake_origin": intake_origin,
    }
    if raw.get("attachment_path"):
        signal["attachment_path"] = raw["attachment_path"]
        signal["attachment_title"] = raw.get("attachment_title") or "Lampiran media sosial"
        signal["attachment_source"] = "Media Sosial"
    return signal
