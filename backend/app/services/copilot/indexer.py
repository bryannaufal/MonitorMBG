"""Build searchable case documents for copilot RAG."""

from __future__ import annotations

from typing import Any

from app import demo_data, seed_data as sd


def _flatten_case(case: dict[str, Any]) -> str:
    score = case.get("score") or {}
    vendor = case.get("vendor") or {}
    case_number = case.get("case_number") or sd.case_number(case.get("case_id") or "")
    parts = [
        f"Kasus {case_number} ({case.get('case_id')}) — {case.get('title')}",
        f"Status: {case.get('status')} | Prioritas: {case.get('priority_label')}",
        f"Vendor: {case.get('vendor_name')} | Wilayah: {case.get('district')}, {case.get('region')}",
        f"Sekolah: {case.get('school')} | Isu: {case.get('issue_category')}",
        f"Ringkasan: {case.get('what_happened') or case.get('summary') or ''}",
        f"Dampak: {case.get('why_it_matters') or ''}",
        (
            f"Skor — dampak {score.get('severity_score')}, keyakinan {score.get('confidence_score')}, "
            f"dapat ditindak {score.get('actionability_score')}, gizi {score.get('nutrition_score')}, "
            f"prioritas {score.get('final_priority_score')}"
        ),
        f"Rekomendasi: {case.get('recommended_action') or ''}",
        f"Penjelasan risiko: {case.get('risk_explanation') or ''}",
    ]

    for sig in (case.get("signals") or [])[:5]:
        parts.append(
            f"Sinyal #{sig.get('id')}: {sig.get('summary')} ({sig.get('source')}, {sig.get('urgency')})"
        )
    for ev in (case.get("evidence") or [])[:5]:
        parts.append(f"Bukti: {ev.get('title')} — {(ev.get('description') or '')[:200]}")
    for rep in (case.get("reports") or [])[:3]:
        parts.append(f"Laporan: {rep.get('title')} — {(rep.get('summary') or '')[:200]}")
    if vendor:
        parts.append(
            f"Profil vendor: risiko {vendor.get('risk_score')}, "
            f"watchlist={vendor.get('watchlist')}, isu berulang: {', '.join(vendor.get('repeated_issue_categories') or [])}"
        )

    return "\n".join(p for p in parts if p and str(p).strip())


def build_case_document(case_id: str) -> str | None:
    """Flatten a case into one text block for embedding."""
    try:
        case = demo_data.case_detail(case_id)
    except Exception:
        return None
    return _flatten_case(case)


def build_case_document_from_payload(case: dict[str, Any]) -> str | None:
    """Build RAG text from a case payload (API or client overlay)."""
    if not case.get("case_id"):
        return None
    return _flatten_case(case)


def document_metadata(case_id: str) -> dict[str, Any]:
    try:
        case = demo_data.case_detail(case_id)
    except Exception:
        return {"case_id": case_id, "source_type": "case", "title": case_id}
    return metadata_from_case(case)


def metadata_from_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = case.get("case_id") or ""
    return {
        "case_id": case_id,
        "source_type": "case",
        "title": case.get("case_number") or sd.case_number(case_id) if case_id else case_id,
        "region": case.get("region"),
        "priority_label": case.get("priority_label"),
        "vendor_name": case.get("vendor_name"),
    }
