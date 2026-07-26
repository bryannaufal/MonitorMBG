"""Append-only runtime intake layer — seed data never mutated for new signals."""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from typing import Any

from app import seed_data as sd

RUNTIME_SIGNALS: list[dict[str, Any]] = []
RUNTIME_ID_START = 9001
_seen_hashes: set[str] = set()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def _text_hash(text: str) -> str:
    return hashlib.sha256(_normalize_text(text).encode()).hexdigest()


def all_signals() -> list[dict[str, Any]]:
    return [*sd.SIGNALS, *RUNTIME_SIGNALS]


def get_signal(signal_id: int) -> dict[str, Any] | None:
    for sig in all_signals():
        if sig["id"] == signal_id:
            return sig
    return None


def next_signal_id() -> int:
    if RUNTIME_SIGNALS:
        return max(s["id"] for s in RUNTIME_SIGNALS) + 1
    return RUNTIME_ID_START


def is_duplicate(text: str) -> bool:
    h = _text_hash(text)
    if h in _seen_hashes:
        return True
    for sig in all_signals():
        if SequenceMatcher(None, _normalize_text(sig.get("text", "")), _normalize_text(text)).ratio() >= 0.88:
            return True
    return False


def append_signal(signal: dict[str, Any]) -> dict[str, Any]:
    _seen_hashes.add(_text_hash(signal.get("text") or signal.get("summary") or ""))
    RUNTIME_SIGNALS.insert(0, signal)
    return signal
