"""Pre-baked assessments for seed signals (ids 1–20) — no Kimi at review time."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app import seed_data as sd

_SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "signal_assessment_seed.json"
_SEED_IDS = frozenset(s["id"] for s in sd.SIGNALS)
_CACHE: dict[int, dict[str, Any]] | None = None

# Kurasi manual untuk foto seed bila vision API tidak dipanggil saat bake.
_PHOTO_NUTRITION_OVERRIDES: dict[int, dict[str, Any]] = {
    19: {
        "nutrition_score": 28,
        "nutrition_reasons": [
            "Foto laporan resmi menunjukkan indikasi kontaminasi/belatung pada porsi",
            "Porsi tampak tidak layak konsumsi — estimasi seed dari bukti foto 4.jpg",
        ],
    },
    20: {
        "nutrition_score": 35,
        "nutrition_reasons": [
            "Unggahan sosmed: dugaan belatung — kualitas gizi sangat rendah jika terkonfirmasi",
            "Estimasi seed dari bukti foto 26.jpg (pra-verifikasi)",
        ],
    },
}


def is_seed_signal(signal: dict[str, Any]) -> bool:
    sid = signal.get("id")
    return isinstance(sid, int) and sid in _SEED_IDS


def _load_cache() -> dict[int, dict[str, Any]]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if not _SEED_PATH.is_file():
        _CACHE = {}
        return _CACHE
    raw = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    _CACHE = {int(k): v for k, v in raw.items()}
    return _CACHE


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in reasons:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def get_seed_signal_assessment(signal_id: int) -> dict[str, Any] | None:
    """Return frozen seed assessment; never calls Kimi."""
    if signal_id not in _SEED_IDS:
        return None
    base = _load_cache().get(signal_id)
    if not base:
        return None
    out = dict(base)
    out["scoring_engine"] = "seed"
    if out.get("reasons"):
        out["reasons"] = _dedupe_reasons(list(out["reasons"]))
    return out
