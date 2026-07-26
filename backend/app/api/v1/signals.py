"""API Kotak Masuk Sinyal (intake) — sinyal pra-verifikasi sebelum kasus.

Termasuk workflow "Tinjau & Bentuk Kasus": pencarian terkait deterministik,
penilaian awal, daftar investigator, dan aksi review (gabung/kasus baru/tunda).
"""

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app import demo_data, review_store

router = APIRouter()


class Assignment(BaseModel):
    investigator: str | None = None
    unit: str | None = None
    urgency: str | None = None
    sla: str | None = None
    reviewer_note: str | None = None
    recommended_action: str | None = None
    secondary_owner: str | None = None
    watchers: list[str] | None = None


class Override(BaseModel):
    operator_adjusted: bool = False
    priority_label: str = "Sedang"
    final_priority_score: int = 45
    severity_score: int | None = None
    confidence_score: int | None = None
    nutrition_concern_score: int | None = None
    cost_anomaly_score: int | None = None
    anomaly_score: int | None = None
    override_reason: str | None = None


class NewCase(BaseModel):
    title: str | None = None
    issue_category: str | None = None
    vendor_id: str | None = None
    vendor_name: str | None = None
    vendor_source_note: str | None = None
    region: str | None = None
    district: str | None = None
    school: str | None = None
    summary: str | None = None
    case_type: str | None = None
    case_subtype: str | None = None
    impact_summary: str | None = None
    handling_strategy: str | None = None
    related_case_id: str | None = None
    case_relationship: str | None = None


class ReviewAction(BaseModel):
    decision: str  # merge | create | defer
    searched_related: bool = False
    target_case_id: str | None = None
    new_case: NewCase | None = None
    defer_reason: str | None = None
    selected_signal_ids: list[int] = []
    selected_evidence_ids: list[int] = []
    assignment: Assignment | None = None
    override: Override | None = None


class UnlinkAction(BaseModel):
    reason: str


@router.get("")
@router.get("/")
async def list_signals(
    source: str | None = Query(default=None),
    status: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    region: str | None = Query(default=None),
    linked: str | None = Query(default=None, description="linked|unlinked"),
):
    """Daftar sinyal intake dengan filter operator.

    Setiap sinyal punya ``case_id`` valid atau ``null`` (belum dibentuk kasus).
    """
    items = demo_data.SIGNALS
    if source:
        items = [s for s in items if source.lower() in s["source"].lower()]
    if status:
        items = [s for s in items if status.lower() in s["status"].lower()]
    if urgency:
        items = [s for s in items if s["urgency"].lower() == urgency.lower()]
    if region:
        items = [s for s in items if region.lower() in (s.get("region") or "").lower()]
    if linked == "linked":
        items = [s for s in items if s.get("case_id")]
    elif linked == "unlinked":
        items = [s for s in items if not s.get("case_id")]
    items = sorted(items, key=lambda s: s["created_at"], reverse=True)
    return {"items": items, "total": len(items)}


@router.get("/investigators")
async def list_investigators(
    region: str | None = Query(default=None),
    district: str | None = Query(default=None),
    school: str | None = Query(default=None),
):
    """Opsi penanggung jawab terfilter; format ``items`` lama tetap kompatibel."""
    options = review_store.assignment_options(region, district, school)
    return {
        "items": [item["name"] for item in options["investigators"]],
        "candidates": options["investigators"],
    }


@router.get("/assignment-options")
async def get_assignment_options(
    region: str | None = Query(default=None),
    district: str | None = Query(default=None),
    school: str | None = Query(default=None),
):
    """Kandidat lokasi, vendor, investigator, dan unit dari registry wilayah."""
    return review_store.assignment_options(region, district, school)


@router.get("/{signal_id}")
async def get_signal(signal_id: int):
    """Ambil satu sinyal. 404 jelas bila tidak ditemukan (tanpa fallback)."""
    return review_store.get_signal(signal_id)


@router.get("/{signal_id}/assessment")
async def get_assessment(signal_id: int):
    """Penilaian awal sistem (pra-verifikasi) untuk sinyal."""
    return review_store.initial_assessment(signal_id)


@router.post("/{signal_id}/related")
async def search_related(signal_id: int):
    """Pencarian sinyal, laporan, dan bukti terkait (deterministik, data internal)."""
    return review_store.find_related(signal_id)


@router.post("/{signal_id}/review")
async def review(signal_id: int, action: ReviewAction):
    """Aksi review: gabungkan / bentuk kasus baru / simpan untuk ditinjau nanti."""
    return review_store.review_signal(signal_id, action.model_dump())


@router.post("/{signal_id}/unlink")
async def unlink(signal_id: int, action: UnlinkAction):
    """Lepaskan relasi signal→kasus dengan alasan; signal kembali ke antrean tinjauan."""
    return review_store.unlink_signal(signal_id, action.model_dump())
