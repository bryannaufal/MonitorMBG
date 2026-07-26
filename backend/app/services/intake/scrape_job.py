"""In-memory scrape job with progress — survives client navigation via polling."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.config import settings
from app.services.intake.social_scraper import scrape_social

logger = logging.getLogger(__name__)


class ScrapePhase(str, Enum):
    IDLE = "idle"
    FETCHING = "fetching"
    SCORING = "scoring"
    DONE = "done"
    ERROR = "error"


@dataclass
class ScrapeJob:
    job_id: str
    phase: ScrapePhase = ScrapePhase.FETCHING
    label: str = "Memulai scrape..."
    current: int = 0
    total: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None


_job: ScrapeJob | None = None
_lock = asyncio.Lock()
_DONE_TTL_SECONDS = 120.0


def _auto_ticket_on_scrape() -> bool:
    return settings.AUTO_TICKET_ON_INTAKE


def is_active() -> bool:
    if _job is None:
        return False
    if _job.phase in (ScrapePhase.FETCHING, ScrapePhase.SCORING):
        return True
    if _job.phase in (ScrapePhase.DONE, ScrapePhase.ERROR) and _job.finished_at:
        return (time.time() - _job.finished_at) < _DONE_TTL_SECONDS
    return False


def is_running() -> bool:
    return _job is not None and _job.phase in (ScrapePhase.FETCHING, ScrapePhase.SCORING)


def to_response() -> dict[str, Any]:
    if _job is None:
        return {"active": False, "phase": ScrapePhase.IDLE.value}

    active = is_active()
    payload: dict[str, Any] = {
        "active": active,
        "job_id": _job.job_id,
        "phase": _job.phase.value,
        "label": _job.label,
        "current": _job.current,
        "total": _job.total,
        "mode": settings.SCRAPER_MODE,
        "auto_ticket": _auto_ticket_on_scrape(),
    }
    if _job.result is not None:
        payload["result"] = _job.result
    if _job.error:
        payload["error"] = _job.error
    return payload


def start() -> ScrapeJob:
    global _job
    _job = ScrapeJob(job_id=str(uuid.uuid4()))
    return _job


async def execute() -> None:
    """Run scrape pipeline; updates global job progress."""
    from app.api.v1.intake import _maybe_auto_ticket

    global _job
    if _job is None:
        return

    job = _job
    try:
        job.phase = ScrapePhase.FETCHING
        job.label = "Mengambil feed sosial media..."
        job.current = 0
        job.total = 0

        result = await scrape_social()
        inserted: list[dict[str, Any]] = result.get("signals") or []
        total = len(inserted)
        job.total = total
        auto_ticket = _auto_ticket_on_scrape()
        logger.info(
            "Scrape fetch done - job=%s inserted=%s skipped=%s origin=%s",
            job.job_id,
            result.get("inserted"),
            result.get("skipped_duplicates"),
            result.get("intake_origin"),
        )

        auto_results: list[dict[str, Any]] = []
        if auto_ticket and total > 0:
            job.phase = ScrapePhase.SCORING
            for idx, signal in enumerate(inserted, start=1):
                job.current = idx
                job.label = f"Menilai sinyal {idx}/{total} (Kimi)..."
                auto = _maybe_auto_ticket(signal, enabled=True)
                if auto:
                    auto_results.append({"signal_id": signal["id"], **auto})
        elif total == 0:
            job.label = "Feed selesai — tidak ada sinyal baru"
        else:
            job.current = total
            job.label = f"{total} sinyal ditambahkan"

        result["auto_tickets"] = auto_results
        job.result = result
        job.phase = ScrapePhase.DONE
        job.label = result.get("message") or "Scrape selesai"
        job.current = total
        job.finished_at = time.time()
        logger.info("Scrape job %s finished - %s", job.job_id, job.label)
    except Exception as exc:
        job.phase = ScrapePhase.ERROR
        job.error = str(exc)
        job.label = "Scrape gagal"
        job.finished_at = time.time()
        logger.warning("Scrape job %s failed: %s", job.job_id, exc)


async def start_background() -> dict[str, Any]:
    async with _lock:
        if is_running():
            logger.info("Scrape already running - returning status job=%s", _job.job_id if _job else "?")
            return to_response()
        job = start()
        logger.info(
            "Scrape started - job=%s mode=%s auto_ticket=%s",
            job.job_id,
            settings.SCRAPER_MODE,
            _auto_ticket_on_scrape(),
        )
        asyncio.create_task(execute())
        return to_response()
