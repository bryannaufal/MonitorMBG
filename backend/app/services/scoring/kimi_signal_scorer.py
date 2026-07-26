"""Kimi (Moonshot AI) severity & actionability for signal risk scoring.

When ``KIMI_API_KEY`` is set, ``score_signal_with_kimi`` calls the API.
Any failure returns ``None`` so ``risk_scorer`` falls back to rules-only.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_CHAT_COMPLETIONS = "/chat/completions"
_MAX_ATTEMPTS = 3


def _http_client() -> httpx.Client:
    """Prefer IPv4 — avoids intermittent getaddrinfo failures on some Windows networks."""
    transport = httpx.HTTPTransport(local_address="0.0.0.0", retries=0)
    return httpx.Client(timeout=settings.KIMI_TIMEOUT_SECONDS, transport=transport)


def _host_label(url: str) -> str:
    return urlparse(url).netloc or url


def _signal_payload(signal: dict[str, Any]) -> str:
    lines = [
        f"source: {signal.get('source') or 'Media Sosial'}",
        f"urgency: {signal.get('urgency') or 'Sedang'}",
        f"issue_category: {signal.get('issue_category') or '-'}",
        f"region: {signal.get('region') or 'Belum teridentifikasi'}",
        f"district: {signal.get('district') or 'Belum teridentifikasi'}",
        f"school: {signal.get('school') or 'Belum teridentifikasi'}",
        f"vendor_id: {signal.get('vendor_id') or '-'}",
        f"has_attachment: {bool(signal.get('attachment_path'))}",
        f"summary: {signal.get('summary') or '-'}",
        f"text: {signal.get('text') or '-'}",
    ]
    return "\n".join(lines)


def _parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _clamp_score(value: Any, default: int = 50) -> int:
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(0, min(100, n))


def _as_reasons(value: Any, fallback: str) -> list[str]:
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return items or [fallback]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return [fallback]


def score_signal_with_kimi(signal: dict[str, Any]) -> dict[str, Any] | None:
    """Return severity + actionability from Kimi, or ``None`` on skip/failure."""
    api_key = (settings.KIMI_API_KEY or "").strip()
    if not api_key:
        return None

    base = settings.KIMI_BASE_URL.rstrip("/")
    model = settings.KIMI_MODEL
    user_prompt = f"""Anda menilai sinyal intake program MBG (Makan Bergizi Gratis) untuk pengawasan pemerintah Indonesia.
Berikan penilaian pra-verifikasi (bukan keputusan final).

Kembalikan HANYA JSON valid dengan field:
- severity_score (integer 0-100)
- actionability_score (integer 0-100)
- severity_reasons (array string, 1-3 item)
- actionability_reasons (array string, 1-3 item)

severity_score: dampak potensial isu (keamanan pangan, kontaminasi, keracunan, higiene, kualitas gizi/porsi).
actionability_score: seberapa siap sinyal ditindak (lokasi/sekolah spesifik, detail konkret, vendor, lampiran).

Sinyal:
{_signal_payload(signal)}
"""

    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Anda asisten analisis risiko MBG. Balas hanya JSON object valid tanpa markdown."
                ),
            },
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    # Kimi Code (`api.kimi.com/coding`) rejects temperature != 1; omit for compatibility.
    if "moonshot" in base:
        body["temperature"] = 0.2

    url = f"{base}{_CHAT_COMPLETIONS}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    signal_id = signal.get("id", "?")
    summary = (signal.get("summary") or signal.get("text") or "-")[:70]
    logger.info(
        "Kimi scoring signal #%s - model=%s host=%s summary=%r",
        signal_id,
        model,
        _host_label(url),
        summary,
    )
    started = time.perf_counter()

    try:
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                with _http_client() as client:
                    resp = client.post(url, headers=headers, json=body)
                    resp.raise_for_status()
                    payload = resp.json()
                break
            except (httpx.ConnectError, httpx.NetworkError, OSError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS:
                    logger.warning(
                        "Kimi scoring network error (%s), retry %s/%s: %s",
                        _host_label(url), attempt, _MAX_ATTEMPTS, exc,
                    )
                    time.sleep(0.8 * attempt)
                    continue
                raise last_exc from exc
        else:
            return None

        choices = payload.get("choices") or []
        if not choices:
            return None
        raw = (choices[0].get("message") or {}).get("content") or ""
        data = _parse_json(raw)
        if not data:
            logger.warning("Kimi scoring: unparseable JSON response")
            return None

        severity = _clamp_score(data.get("severity_score"))
        actionability = _clamp_score(data.get("actionability_score"))
        logger.info(
            "Kimi scoring signal #%s OK - severity=%s actionability=%s (%.1fs)",
            signal_id,
            severity,
            actionability,
            time.perf_counter() - started,
        )
        return {
            "severity_score": severity,
            "actionability_score": actionability,
            "severity_reasons": _as_reasons(
                data.get("severity_reasons"), "Penilaian dampak isu oleh Kimi.",
            ),
            "actionability_reasons": _as_reasons(
                data.get("actionability_reasons"), "Penilaian kesiapan tindak oleh Kimi.",
            ),
        }
    except httpx.HTTPStatusError as exc:
        code = exc.response.status_code
        detail = ""
        try:
            detail = (exc.response.json().get("error") or {}).get("message", "")[:200]
        except Exception:
            pass
        logger.warning("Kimi scoring HTTP %s: %s", code, detail or exc.response.reason_phrase)
        return None
    except Exception as exc:
        logger.warning("Kimi scoring failed: %s", exc)
        return None
