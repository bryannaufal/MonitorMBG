"""Adapter respons API MonitorMBG di atas sumber kanonik ``seed_data``.

Semua respons diturunkan dari ``seed_data`` (satu sumber kebenaran). Bentuk
objek dipertahankan agar selaras dengan tipe frontend. Tidak ada fallback
diam-diam ke kasus lain: id tak dikenal menghasilkan 404 yang jelas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app import seed_data as sd

DEMO_NOTICE = sd.GOVERNANCE_NOTICE

# Ekspor mentah (dipakai endpoint & vendor_profile).
VENDORS = sd.VENDORS
LOCATION_REGISTRY = sd.LOCATION_REGISTRY
INVESTIGATOR_REGISTRY = sd.INVESTIGATOR_REGISTRY
UNIT_REGISTRY = sd.UNIT_REGISTRY
SIGNALS = sd.SIGNALS
EVIDENCE = sd.EVIDENCE
SCORES = sd.RISK
TICKETS = sd.TICKETS
AUDIT_TRAIL = sd.AUDIT
REGIONAL_HEATMAP = sd.REGIONAL_HEATMAP
TRENDS = sd.TRENDS
ANOMALIES = sd.ANOMALIES

_vendor_lookup = sd.VENDOR_BY_ID


# ── Kompatibilitas: "complaints" = signal dari kanal publik ──────────────
def _signal_as_complaint(sig: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": sig["id"],
        "case_id": sig.get("case_id"),
        "source": sig["source"],
        "source_confidence": sig["source_confidence"],
        "summary": sig["summary"],
        "text": sig["text"],
        "issue_category": sig.get("issue_category", "belum diklasifikasi"),
        "sentiment": "negative",
        "severity_score": sd.RISK_BY_CASE[sig["case_id"]]["final_priority_score"] if sig.get("case_id") else 40,
        "region": sig.get("region", "Belum teridentifikasi"),
        "district": sig.get("district", "Belum teridentifikasi"),
        "school": sig.get("school", "Belum teridentifikasi"),
        "vendor_id": sig.get("vendor_id"),
        "vendor_name": sig.get("vendor_name", "Belum teridentifikasi"),
        "status": sig["status"],
        "urgency": sig["urgency"],
        "anomaly_tag": "Lonjakan" if sig.get("case_id") in {"case-001", "case-002"} else None,
        "created_at": sig["created_at"],
    }


COMPLAINTS = [_signal_as_complaint(s) for s in SIGNALS]


# ── Laporan resmi & laporan harian (satu per kasus) ──────────────────────
def _build_reports() -> list[dict[str, Any]]:
    out = []
    for idx, case in enumerate(sd.CASES, start=1):
        vendor = _vendor_lookup[case["vendor_id"]]
        out.append({
            "id": idx,
            "case_id": case["case_id"],
            "report_code": f"RPT-MBG-2026-{idx:03d}",
            "reporter_type": "Operator Sekolah" if idx % 2 else "Pengawas Distrik",
            "school": case["school"],
            "region": vendor["region"],
            "district": vendor["district"],
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "submitted_at": case["created_at"],
            "summary": f"Paket laporan resmi untuk {vendor['name']} mencakup distribusi menu dan tinjauan bukti.",
            "evidence_count": len([e for e in EVIDENCE if e["case_id"] == case["case_id"]]),
            "status": case["status"],
            "completeness_score": max(45, 92 - idx * 4),
            "linked_ticket_id": sd.TICKET_BY_CASE[case["case_id"]]["id"],
            "linked_risk_score": vendor["risk_score"],
        })
    return out


REPORTS = _build_reports()


def _build_daily_reports() -> list[dict[str, Any]]:
    out = []
    for idx, case in enumerate(sd.CASES, start=1):
        vendor = _vendor_lookup[case["vendor_id"]]
        mismatch = case["issue_category"] in {"ketidaksesuaian menu", "porsi protein kurang", "buah/susu tidak lengkap"}
        cost_flag = case["issue_category"] == "anomali biaya"
        out.append({
            "id": idx,
            "case_id": case["case_id"],
            "vendor_id": vendor["id"],
            "vendor_name": vendor["name"],
            "school": case["school"],
            "region": vendor["region"],
            "planned_menu": "Nasi, ayam, sayur, buah, susu",
            "actual_menu": "Nasi, telur kecil, sayur" if case["case_id"] == "case-001" else "Nasi, ayam, sayur, buah",
            "delivery_timestamp": case["created_at"],
            "expected_timestamp": case["created_at"],
            "portion_count": vendor["daily_meal_volume"] // max(1, len(vendor["assigned_schools"])),
            "photo_evidence_count": len([e for e in EVIDENCE if e["case_id"] == case["case_id"] and e["type"] == "photo"]),
            "document_complete": case["issue_category"] != "dokumentasi belum lengkap",
            "photo_verification": "Ketidaksesuaian Menu" if mismatch else "Perlu Verifikasi",
            "verification_status": "Ditandai" if mismatch or cost_flag else "Sedang Ditinjau",
            "duplicate_indicator": case["issue_category"] == "indikasi foto duplikat",
            "mismatch_indicator": mismatch,
            "nutrition_estimate": {"calories": 505 if case["case_id"] == "case-001" else 540,
                                    "protein_g": 11 if case["case_id"] == "case-001" else 16,
                                    "carbs_g": 64, "fat_g": 11},
            "cost_estimate": {"cost_per_portion": 15800 if cost_flag or case["case_id"] == "case-001" else 13600,
                               "standard_budget": 15000, "cost_anomaly_flag": cost_flag or case["case_id"] == "case-001"},
            "recommended_follow_up": vendor["recommended_action"],
        })
    return out


DAILY_REPORTS = _build_daily_reports()


# ── Helper respons ───────────────────────────────────────────────────────
def list_response(items: list[dict[str, Any]], page: int = 1, size: int = 50) -> dict[str, Any]:
    start = (page - 1) * size
    return {"items": items[start:start + size], "total": len(items), "page": page, "size": size}


def get_or_404(items: list[dict[str, Any]], item_id: str | int, label: str = "Item") -> dict[str, Any]:
    needle = str(item_id)
    for item in items:
        if str(item.get("id")) == needle:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} '{item_id}' tidak ditemukan")


def overview() -> dict[str, Any]:
    high_risk = len([r for r in SCORES if r["final_priority_score"] >= 65])
    open_tickets = len([t for t in TICKETS if t["status"] != "Selesai"])
    return {
        "total_reports": len(REPORTS) + len(DAILY_REPORTS),
        "public_signals": len(SIGNALS),
        "high_risk_cases": high_risk,
        "average_triage_time": "18 jam",
        "ticket_response_rate": 86,
        "public_signal_spike": "+31%",
        "open_tickets": open_tickets,
        "vendors_on_watchlist": len([v for v in VENDORS if v["watchlist_status"] in {"Kritis", "Tinggi"}]),
        "ai_notice": DEMO_NOTICE,
        "top_region": max(REGIONAL_HEATMAP, key=lambda i: i["risk_score"])["region"],
    }


def vendor_profile(vendor_id: str) -> dict[str, Any]:
    vendor = get_or_404(VENDORS, vendor_id, "Vendor")
    return {
        **vendor,
        "cases": [c for c in oversight_cases() if c["vendor_id"] == vendor_id],
        "linked_complaints": [c for c in COMPLAINTS if c["vendor_id"] == vendor_id],
        "linked_reports": [r for r in REPORTS if r["vendor_id"] == vendor_id],
        "linked_daily_reports": [d for d in DAILY_REPORTS if d["vendor_id"] == vendor_id],
        "ticket_history": [t for t in TICKETS if t["linked_vendor_id"] == vendor_id],
        "nutrition_cost_anomalies": [d for d in DAILY_REPORTS if d["vendor_id"] == vendor_id],
        "audit_notes": [a for a in AUDIT_TRAIL if a["case_id"] in {c["case_id"] for c in sd.CASES if c["vendor_id"] == vendor_id}],
        "ai_notice": DEMO_NOTICE,
    }


# ── Kasus (investigation hub) ────────────────────────────────────────────
def _build_case(case: dict[str, Any]) -> dict[str, Any]:
    cid = case["case_id"]
    vendor = _vendor_lookup[case["vendor_id"]]
    vendor_name = case.get("vendor_name_override") or vendor["name"]
    region = case.get("region") or vendor["region"]
    district = case.get("district") or vendor["district"]
    complaints = [c for c in COMPLAINTS if c["case_id"] == cid]
    reports = [r for r in REPORTS if r["case_id"] == cid]
    daily_reports = [d for d in DAILY_REPORTS if d["case_id"] == cid]
    # Bukti yang relasinya dilepas dari kasus tidak lagi tampil pada daftar
    # aktif; barisnya tetap ada untuk audit dan asetnya tidak dihapus.
    evidence = [e for e in EVIDENCE if e["case_id"] == cid and not e.get("unlinked_from_case")]
    ticket = sd.TICKET_BY_CASE.get(cid)
    score = sd.RISK_BY_CASE[cid]
    audit_events = [a for a in AUDIT_TRAIL if a["case_id"] == cid]
    signals_count = len([s for s in SIGNALS if s.get("case_id") == cid])
    what_happened = (
        f"MonitorMBG mengelompokkan {signals_count} sinyal intake untuk {vendor_name} ke dalam "
        f"{sd.case_number(cid)}. Paket menggabungkan aduan publik, laporan resmi, bukti harian vendor, dan sinyal penilaian."
    )
    why_it_matters = (
        f"Kasus ini menyangkut {case['school']} di {district}, {region} dan dapat "
        f"mengindikasikan {case['issue_category']} terkait vendor dengan skor risiko {vendor['risk_score']}."
    )
    return {
        "id": cid,
        "case_id": cid,
        "case_number": sd.case_number(cid),
        "title": case["title"],
        "priority_label": case["priority_label"],
        "status": case["status"],
        "vendor_id": vendor["id"],
        "vendor_name": vendor_name,
        "vendor_source_note": case.get("vendor_source_note"),
        "region": region,
        "district": district,
        "school": case["school"],
        "issue_category": case["issue_category"],
        "sla_status": f"SLA {ticket['sla']}" if ticket else "SLA 72h",
        "assigned_unit": case.get("assigned_unit") or (ticket["assigned_unit"] if ticket else "Unit Pengawasan Vendor MBG Nasional"),
        "assigned_investigator": case.get("assigned_investigator"),
        "recommended_action": score["recommended_action"],
        "summary": what_happened,
        "what_happened": what_happened,
        "why_it_matters": why_it_matters,
        "risk_explanation": score["explanation"],
        "signals_count": signals_count,
        "evidence_count": len(evidence),
        "ticket_id": ticket["id"] if ticket else None,
        "created_at": case["created_at"],
        "updated_at": case["updated_at"],
        "vendor": vendor,
        "signals": [s for s in SIGNALS if s.get("case_id") == cid],
        "complaints": complaints,
        "reports": reports,
        "daily_reports": daily_reports,
        "evidence": evidence,
        "score": score,
        "ticket": ticket,
        "copilot_sources": [
            {"label": "Kasus", "source_type": "case", "source_id": cid, "title": sd.case_number(cid)},
            {"label": "Vendor", "source_type": "vendor", "source_id": vendor["id"], "title": vendor["name"]},
            {"label": "Skor", "source_type": "score", "source_id": score["id"], "title": f"Skor {sd.case_number(cid)}"},
        ],
        "audit_events": audit_events,
        "ai_notice": DEMO_NOTICE,
    }


def oversight_cases() -> list[dict[str, Any]]:
    cases = [_build_case(c) for c in sd.CASES]
    return sorted(cases, key=lambda i: i["score"]["final_priority_score"], reverse=True)


def case_detail(case_id: str) -> dict[str, Any]:
    case = sd.CASE_BY_ID.get(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Kasus '{case_id}' tidak ditemukan")
    return _build_case(case)


# ── Copilot (asisten ringkasan kasus, terbatas) ──────────────────────────
def copilot_answer(message: str, conversation_id: str | None = None) -> dict[str, Any]:
    query = message.lower()
    top = sorted(SCORES, key=lambda i: i["final_priority_score"], reverse=True)[:3]
    top_vendor = max(VENDORS, key=lambda v: v["risk_score"])
    sources: list[dict[str, Any]] = []

    if any(k in query for k in ("gizi", "protein", "nutrition")):
        related = [s for s in SCORES if s["nutrition_concern_score"] >= 70][:3] or top
        answer = (
            "Anomali terkait gizi terkonsentrasi pada kasus berisiko tinggi dengan estimasi protein rendah "
            "atau bukti menu belum lengkap. Sinyal terkuat adalah "
            f"{related[0]['vendor_name']} dan tetap memerlukan tinjauan operator."
        )
        sources = _score_sources(related)
    elif any(k in query for k in ("wilayah", "region")):
        region = max(REGIONAL_HEATMAP, key=lambda i: i["risk_score"])
        answer = (f"{region['region']} memiliki skor risiko regional tertinggi ({region['risk_score']}) "
                  f"dengan {region['complaint_count']} sinyal dan {region['high_priority_cases']} kasus prioritas tinggi.")
        sources = [{"title": "Heatmap Regional", "source_type": "analytics", "source_id": region["region"], "relevance_score": 0.92}]
    elif any(k in query for k in ("bukti", "evidence")):
        answer = ("Paket bukti menggabungkan foto, dokumen, dan metadata. Skor OCR, kecocokan gambar-teks, "
                  "indikasi duplikat, dan catatan peninjau adalah sinyal pra-verifikasi yang wajib ditinjau operator.")
        sources = [{"title": e["title"], "source_type": "evidence", "source_id": e["id"], "relevance_score": e["confidence_score"]} for e in EVIDENCE[:4]]
    elif any(k in query for k in ("tindak", "operator", "next")):
        answer = ("Langkah berikutnya: prioritaskan tiket Kritis dan Tinggi, minta bukti yang kurang, "
                  "tugaskan verifikasi lapangan ke unit terkait, dan catat setiap perubahan status di jejak audit.")
        sources = _ticket_sources(TICKETS[:3])
    elif any(k in query for k in ("vendor", "watchlist", "pantauan")):
        answer = (f"{top_vendor['name']} adalah vendor berisiko tertinggi (skor {top_vendor['risk_score']}) "
                  f"dengan isu berulang: {', '.join(top_vendor['repeated_issue_categories'])}. "
                  f"Rekomendasi: {top_vendor['recommended_action']}")
        sources = [{"title": top_vendor["name"], "source_type": "vendor", "source_id": top_vendor["id"], "relevance_score": 0.95}]
    else:
        answer = ("Kasus prioritas tertinggi: "
                  + ", ".join(f"{sd.case_number(s['case_id'])} ({s['vendor_name']}, {s['final_priority_score']})" for s in top)
                  + ". Ini sintesis berbantuan AI dan memerlukan tinjauan operator.")
        sources = _score_sources(top)

    return {
        "answer": f"{answer}\n\n{DEMO_NOTICE}",
        "sources": sources,
        "confidence": 0.82,
        "conversation_id": conversation_id or "demo-conversation",
    }


def _score_sources(scores: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "title": f"Hasil penilaian {sd.case_number(s['case_id'])}",
        "content_snippet": s["explanation"][:180],
        "source_type": "score", "source_id": s["id"],
        "relevance_score": round(s["final_priority_score"] / 100, 2),
    } for s in scores]


def _ticket_sources(tickets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "title": t["title"], "content_snippet": t["recommended_action"],
        "source_type": "ticket", "source_id": t["id"],
        "relevance_score": round(t["priority"] / 100, 2),
    } for t in tickets]
