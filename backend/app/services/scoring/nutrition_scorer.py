"""Nutrition (GIZI) scoring — rules demo + optional Kimi vision for live."""

from __future__ import annotations

import base64
import logging
import re
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.services.intake.uploads import INTAKE_MEDIA_BASE, UPLOAD_DIR
from app.services.scoring.kimi_signal_scorer import (
    _CHAT_COMPLETIONS,
    _as_reasons,
    _clamp_score,
    _host_label,
    _http_client,
    _parse_json,
)

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_EVIDENCE_DIR = _REPO_ROOT / "Dataset Gambar"
_MAX_IMAGE_BYTES = 4 * 1024 * 1024

_LOW_NUTRITION = (
    "belatung", "keracunan", "kontaminasi", "busuk", "basi", "higen", "hygiene",
    "cacing", "jamur", "porsi kecil", "protein rendah", "kurang gizi", "tidak bergizi",
    "makanan basi", "tidak layak", "mencurigakan",
)
_HIGH_NUTRITION = (
    "protein", "sayur", "buah", "menu lengkap", "bergizi", "nutrisi cukup",
    "porsi cukup", "gizi baik", "telur", "daging", "susu",
)


def _text_blob(signal: dict[str, Any]) -> str:
    parts = [
        signal.get("summary") or "",
        signal.get("text") or "",
        signal.get("issue_category") or "",
        signal.get("attachment_title") or "",
    ]
    return " ".join(parts).lower()


def _resolve_image_file(attachment_path: str) -> Path | None:
    """Map public attachment URL to file on disk."""
    path = attachment_path.strip()
    if not path:
        return None
    if path.startswith(INTAKE_MEDIA_BASE + "/"):
        candidate = UPLOAD_DIR / Path(path).name
        return candidate if candidate.is_file() else None
    if path.startswith("/evidence-media/"):
        candidate = _EVIDENCE_DIR / Path(path).name
        return candidate if candidate.is_file() else None
    candidate = Path(path)
    if candidate.is_file():
        return candidate
    return None


def _image_data_url(path: Path) -> str | None:
    data = path.read_bytes()
    if len(data) > _MAX_IMAGE_BYTES:
        logger.warning("Nutrition vision skipped — image too large (%s bytes): %s", len(data), path.name)
        return None
    suffix = path.suffix.lower()
    mime = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/jpeg")
    encoded = base64.standard_b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def score_nutrition_rules(signal: dict[str, Any]) -> tuple[int, list[str]]:
    """Estimasi gizi dari teks/deskripsi bila ada lampiran (mode demo / fallback)."""
    score = 68
    reasons: list[str] = ["Lampiran foto tersedia — estimasi pra-verifikasi dari deskripsi isu"]

    blob = _text_blob(signal)
    category = (signal.get("issue_category") or "").lower()

    hits_low = [kw for kw in _LOW_NUTRITION if kw in blob]
    hits_high = [kw for kw in _HIGH_NUTRITION if kw in blob]

    for kw in hits_low:
        score -= 12
        reasons.append(f"Indikasi negatif pada teks: '{kw}'")
    for kw in hits_high:
        score += 6
        reasons.append(f"Indikasi positif pada teks: '{kw}'")

    if "keamanan pangan" in category or "keracunan" in category:
        score -= 15
        reasons.append("Kategori isu berdampak pada keamanan/gizi porsi")
    elif "gizi" in category or "porsi" in category or "nutrisi" in category:
        score -= 10
        reasons.append("Kategori isu terkait gizi/porsi")

    if "protein rendah" in blob or re.search(r"protein\s*(rendah|kurang)", blob):
        score -= 10
        reasons.append("Dugaan protein rendah pada deskripsi")

    score = max(15, min(92, score))
    return score, reasons[:4]


def score_nutrition_with_kimi(signal: dict[str, Any]) -> dict[str, Any] | None:
    """Vision call — estimasi kualitas gizi/porsi dari foto + konteks teks."""
    api_key = (settings.KIMI_API_KEY or "").strip()
    if not api_key:
        return None

    attachment = signal.get("attachment_path")
    if not attachment:
        return None

    image_path = _resolve_image_file(attachment)
    if image_path is None:
        logger.info("Nutrition vision skipped — file not found: %s", attachment)
        return None

    data_url = _image_data_url(image_path)
    if not data_url:
        return None

    base = settings.KIMI_BASE_URL.rstrip("/")
    model = (settings.KIMI_VISION_MODEL or settings.KIMI_MODEL).strip()
    context = _text_blob(signal)

    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Anda menilai kualitas gizi/porsi MBG dari foto dan konteks laporan "
                "(pra-verifikasi, bukan keputusan final).\n"
                "Kembalikan HANYA JSON valid dengan field:\n"
                "- nutrition_score (integer 0-100, 100=sangat baik/bergizi, 0=sangat buruk/tidak layak)\n"
                "- nutrition_reasons (array string, 1-3 item)\n\n"
                f"Konteks laporan:\n{context or '-'}"
            ),
        },
        {"type": "image_url", "image_url": {"url": data_url}},
    ]

    body: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Anda analis gizi program MBG Indonesia. Balas hanya JSON object valid tanpa markdown.",
            },
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }
    if "moonshot" in base:
        body["temperature"] = 0.2

    url = f"{base}{_CHAT_COMPLETIONS}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    signal_id = signal.get("id", "?")

    logger.info(
        "Kimi nutrition vision signal #%s - model=%s host=%s file=%s",
        signal_id, model, _host_label(url), image_path.name,
    )

    try:
        with _http_client() as client:
            resp = client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            payload = resp.json()
        choices = payload.get("choices") or []
        if not choices:
            return None
        raw = (choices[0].get("message") or {}).get("content") or ""
        data = _parse_json(raw)
        if not data:
            logger.warning("Kimi nutrition: unparseable JSON")
            return None
        score = _clamp_score(data.get("nutrition_score"), default=55)
        return {
            "nutrition_score": score,
            "nutrition_reasons": _as_reasons(
                data.get("nutrition_reasons"), "Estimasi gizi dari foto oleh Kimi.",
            ),
        }
    except httpx.HTTPStatusError as exc:
        logger.warning("Kimi nutrition HTTP %s: %s", exc.response.status_code, exc.response.reason_phrase)
        return None
    except Exception as exc:
        logger.warning("Kimi nutrition failed: %s", exc)
        return None


def score_nutrition(signal: dict[str, Any]) -> tuple[int | None, list[str], str]:
    """Return (nutrition_score, reasons, engine).

    - Tanpa lampiran → (None, [], 'none')
    - fixture / tanpa API key → rules dari deskripsi
    - live + key → Kimi vision, fallback rules
    """
    if not signal.get("attachment_path"):
        return None, [], "none"

    use_vision = (
        (settings.SCRAPER_MODE or "").lower() == "live"
        and bool((settings.KIMI_API_KEY or "").strip())
    )

    if use_vision:
        kimi = score_nutrition_with_kimi(signal)
        if kimi:
            return kimi["nutrition_score"], kimi["nutrition_reasons"], "kimi_vision"

    score, reasons = score_nutrition_rules(signal)
    return score, reasons, "rules"
