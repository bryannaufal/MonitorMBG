"""Public intake API — formulir publik & evaluasi auto-ticket."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile

from app.runtime_store import append_signal, is_duplicate
from app.services.intake.normalizer import from_public_form
from app.services.intake import scrape_job
from app.services.intake.uploads import save_public_intake_photo
from app.services.scoring.risk_scorer import score_signal
from app.services.ticketing import auto_ticket_gate, ticket_service

router = APIRouter()
logger = logging.getLogger(__name__)


def _maybe_auto_ticket(signal: dict[str, Any], *, enabled: bool) -> dict[str, Any] | None:
    if not enabled:
        return None
    risk = score_signal(signal)
    eligible, reason = auto_ticket_gate.evaluate(signal, risk)
    if not eligible:
        return {"auto_ticket_created": False, "gate_reason": reason, "risk": risk}
    return ticket_service.create_auto_from_signal(signal["id"])


@router.post("/form")
async def submit_public_form(request: Request):
    """Formulir publik — tanpa login. Append-only ke runtime signals."""
    form = await request.form()
    description = str(form.get("description") or "").strip()
    if len(description) < 10:
        raise HTTPException(status_code=400, detail="Deskripsi laporan minimal 10 karakter.")
    if len(description) > 2000:
        raise HTTPException(status_code=400, detail="Deskripsi laporan maksimal 2000 karakter.")

    issue_category = str(form.get("issue_category") or "").strip() or None
    region = str(form.get("region") or "").strip() or None
    district = str(form.get("district") or "").strip() or None
    school = str(form.get("school") or "").strip() or None

    if is_duplicate(description):
        return {
            "duplicate": True,
            "message": "Laporan serupa sudah ada di antrean.",
            "ai_notice": "Duplikat dicegah; data demo seed tidak diubah.",
        }

    payload: dict[str, Any] = {
        "description": description,
        "issue_category": issue_category,
        "region": region,
        "district": district,
        "school": school,
    }

    photo = form.get("photo")
    if isinstance(photo, UploadFile) and photo.filename:
        path, title = await save_public_intake_photo(photo)
        payload["attachment_path"] = path
        payload["attachment_title"] = title

    signal = from_public_form(payload)
    append_signal(signal)
    return {
        "duplicate": False,
        "signal": signal,
        "message": "Laporan berhasil diterima. Terima kasih — tim pengawasan akan meninjau di Kotak Masuk Sinyal.",
        "ai_notice": "Laporan publik masuk sebagai sinyal pra-verifikasi. Tiket/kasus dibuat setelah operator meninjau.",
    }


@router.post("/scrape")
async def trigger_scrape():
    """Mulai scrape async; client poll GET /intake/scrape/status untuk progress."""
    return await scrape_job.start_background()


@router.get("/scrape/status")
async def scrape_status():
    """Status job scrape aktif atau hasil terakhir (TTL singkat)."""
    return scrape_job.to_response()
