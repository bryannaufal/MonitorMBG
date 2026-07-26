"""Social intake scraper — fixture (default) or live (twitterapi.io / RSS)."""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import httpx

from app.config import settings
from app.runtime_store import append_signal, is_duplicate
from app.services.intake.normalizer import from_social_raw

logger = logging.getLogger(__name__)

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "social_feed_fixture.json"

_ORIGIN_LABELS = {
    "scraper_fixture": "data simulasi",
    "scraper_live": "RSS live",
    "scraper_twitter": "X live",
}


def _origin_label(origin: str) -> str:
    return _ORIGIN_LABELS.get(origin, origin)


def _load_fixture() -> list[dict[str, Any]]:
    if not FIXTURE_PATH.is_file():
        return []
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _keywords_match(text: str) -> bool:
    blob = text.lower()
    keys = [k.strip() for k in settings.SCRAPER_KEYWORDS.split(",") if k.strip()]
    return any(k in blob for k in keys) if keys else True


async def _fetch_live_rss() -> list[dict[str, Any]]:
    url = settings.SCRAPER_RSS_URL
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    root = ET.fromstring(resp.text)
    items: list[dict[str, Any]] = []
    for item in root.findall(".//item")[:10]:
        title = (item.findtext("title") or "").strip()
        desc = re.sub(r"<[^>]+>", " ", item.findtext("description") or "")
        text = f"{title}. {desc}".strip()
        if not text or not _keywords_match(text):
            continue
        items.append({
            "text": text[:500],
            "summary": title[:120] or text[:120],
            "region": "Belum teridentifikasi",
            "source_confidence": 0.45,
            "created_at": item.findtext("pubDate"),
        })
    return items


async def _fetch_twitterapi_io() -> list[dict[str, Any]]:
    if not settings.TWITTERAPI_IO_API_KEY:
        raise ValueError("TWITTERAPI_IO_API_KEY belum di-set di .env")

    base = settings.TWITTERAPI_IO_BASE_URL.rstrip("/")
    url = f"{base}/twitter/tweet/advanced_search"
    headers = {"X-API-Key": settings.TWITTERAPI_IO_API_KEY}
    params = {
        "query": settings.TWITTERAPI_IO_SEARCH_QUERY,
        "queryType": settings.TWITTERAPI_IO_QUERY_TYPE,
    }

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers, params=params)
        resp.raise_for_status()
    data = resp.json()
    tweets = data.get("tweets") or data.get("data") or []

    items: list[dict[str, Any]] = []
    for tweet in tweets[: settings.SCRAPER_TWITTER_MAX_RESULTS]:
        text = (tweet.get("text") or tweet.get("full_text") or "").strip()
        if not text:
            continue
        if not _keywords_match(text):
            continue
        items.append({
            "text": text[:500],
            "summary": text[:120],
            "region": "Belum teridentifikasi",
            "source_confidence": 0.38,
            "created_at": tweet.get("createdAt") or tweet.get("created_at"),
            "external_id": tweet.get("id") or tweet.get("id_str"),
        })
    return items


def _parse_live_providers(raw: str) -> list[str]:
    """Parse SCRAPER_LIVE_PROVIDER — supports twitter, rss, or comma list (order preserved)."""
    value = raw.strip().lower()
    if value == "both":
        return ["twitter", "rss"]
    return [p.strip() for p in value.split(",") if p.strip()]


async def _fetch_one_provider(provider: str) -> tuple[list[dict[str, Any]], str]:
    if provider == "twitter":
        return await _fetch_twitterapi_io(), "scraper_twitter"
    if provider == "rss":
        return await _fetch_live_rss(), "scraper_live"
    raise ValueError(f"SCRAPER_LIVE_PROVIDER tidak dikenal: {provider}")


async def _fetch_live() -> tuple[list[dict[str, Any]], str, str | None]:
    """Fetch one or more live providers; each raw item carries its own _intake_origin."""
    providers = _parse_live_providers(settings.SCRAPER_LIVE_PROVIDER)
    if not providers:
        raise ValueError("SCRAPER_LIVE_PROVIDER kosong")

    combined: list[dict[str, Any]] = []
    used: list[str] = []
    errors: list[str] = []

    for provider in providers:
        try:
            logger.info("Scrape fetching live provider: %s", provider)
            items, origin = await _fetch_one_provider(provider)
            logger.info("Scrape provider %s returned %s items", provider, len(items))
            for item in items:
                tagged = dict(item)
                tagged["_intake_origin"] = origin
                combined.append(tagged)
            used.append(provider)
        except Exception as exc:
            errors.append(f"{provider}: {exc}")

    if not combined:
        raise ValueError("; ".join(errors) if errors else "Tidak ada provider live yang berhasil")

    summary_origin = used[0] if len(used) == 1 else "+".join(used)
    partial_error = "; ".join(errors) if errors else None
    return combined, summary_origin, partial_error


async def scrape_social(*, mode: str | None = None) -> dict[str, Any]:
    """Scrape/simulate social intake; append new signals (never touches seed)."""
    mode = (mode or settings.SCRAPER_MODE).lower()
    intake_origin = "scraper_fixture"
    raw_items: list[dict[str, Any]] = []
    live_error: str | None = None

    if mode == "live":
        try:
            raw_items, intake_origin, partial_error = await _fetch_live()
            live_error = partial_error
        except Exception as exc:
            live_error = str(exc)
            logger.warning("Scrape live fetch failed, using fixture: %s", exc)
            raw_items = _load_fixture()
            intake_origin = "scraper_fixture"
    else:
        logger.info("Scrape using fixture data")
        raw_items = _load_fixture()

    if not raw_items and mode == "live":
        raw_items = _load_fixture()
        intake_origin = "scraper_fixture"

    inserted: list[dict[str, Any]] = []
    skipped = 0
    for raw in raw_items:
        text = raw.get("text") or raw.get("summary") or ""
        if is_duplicate(text):
            skipped += 1
            continue
        item_origin = raw.pop("_intake_origin", None) or intake_origin
        signal = from_social_raw(raw, intake_origin=item_origin)
        append_signal(signal)
        inserted.append(signal)

    return {
        "mode": mode,
        "live_provider": settings.SCRAPER_LIVE_PROVIDER if mode == "live" else None,
        "intake_origin": intake_origin,
        "inserted": len(inserted),
        "skipped_duplicates": skipped,
        "signals": inserted,
        "live_fallback": live_error,
        "message": (
            f"{len(inserted)} sinyal baru ditambahkan ({_origin_label(intake_origin)})."
            if inserted
            else "Tidak ada sinyal baru (duplikat atau feed kosong)."
        ),
    }
