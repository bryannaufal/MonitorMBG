"""Ticket creation — auto (from signal) and manual (from existing case)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app import seed_data as sd
from app.runtime_store import get_signal
from app.services.scoring.risk_scorer import score_signal
from app.services.ticketing import auto_ticket_gate

UNKNOWN = "Belum teridentifikasi"
URGENCY_TO_SLA = {"Kritis": "24h", "Tinggi": "24h", "Sedang": "48h", "Rendah": "72h"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_case_id() -> str:
    nums = [int("".join(ch for ch in c["case_id"] if ch.isdigit()) or 0) for c in sd.CASES]
    return f"case-{(max(nums, default=0) + 1):03d}"


def _next_ticket_id() -> str:
    nums = []
    for t in sd.TICKETS:
        part = t["id"].replace("tkt-", "")
        if part.isdigit():
            nums.append(int(part))
    return f"tkt-{(max(nums, default=0) + 1):03d}"


def _add_audit(case_id: str, event_type: str, description: str, ticket_id: str | None = None) -> dict[str, Any]:
    event = {
        "id": (max((a["id"] for a in sd.AUDIT), default=0) + 1),
        "case_id": case_id,
        "ticket_id": ticket_id,
        "event_type": event_type,
        "actor": "Sistem Intake",
        "role": "Sistem",
        "description": description,
        "timestamp": _now(),
    }
    sd.AUDIT.insert(0, event)
    return event


def _register_risk(case_id: str, vendor: dict, assess: dict[str, Any], *, region: str) -> dict[str, Any]:
    risk = {
        "id": (max((r["id"] for r in sd.RISK), default=0) + 1),
        "case_id": case_id,
        "vendor_id": vendor["id"],
        "vendor_name": vendor["name"],
        "region": region,
        "severity_score": assess["severity_score"],
        "confidence_score": assess["confidence_score"],
        "actionability_score": assess.get("actionability_score", 30),
        "nutrition_score": assess.get("nutrition_score"),
        "final_priority_score": assess["final_priority_score"],
        "priority_label": assess["priority_label"],
        "explanation": assess.get("explanation", ""),
        "recommended_action": assess.get("recommended_action", "Tinjau operator diperlukan."),
        "computed_at": _now(),
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }
    sd.RISK.append(risk)
    sd.RISK_BY_CASE[case_id] = risk
    return risk


def _add_evidence_from_signal(case_id: str, signal: dict[str, Any]) -> dict[str, Any] | None:
    path = signal.get("attachment_path")
    if not path:
        return None
    ev = {
        "id": (max((e["id"] for e in sd.EVIDENCE), default=0) + 1),
        "case_id": case_id,
        "signal_id": signal["id"],
        "type": "photo",
        "title": signal.get("attachment_title") or "Lampiran sinyal",
        "file_path": path,
        "linked_entity": sd.case_number(case_id),
        "source": signal.get("attachment_source") or signal.get("source") or "Sinyal",
        "ocr_result": None,
        "image_text_match_score": None,
        "duplicate_score": None,
        "confidence_score": round(float(signal.get("source_confidence") or 0.5), 2),
        "review_status": "Perlu Ditinjau",
        "reviewer_note": "Lampiran intake otomatis — pra-verifikasi, bukan bukti final.",
        "created_at": _now(),
    }
    sd.EVIDENCE.append(ev)
    return ev


def _build_ticket(
    case_id: str,
    case: dict[str, Any],
    vendor: dict,
    assess: dict[str, Any],
    *,
    origin: str,
    priority_mode: str,
    auto_reason: str | None = None,
) -> dict[str, Any]:
    label = assess["priority_label"]
    tid = _next_ticket_id()
    ev_ids = [e["id"] for e in sd.EVIDENCE if e["case_id"] == case_id]
    ticket: dict[str, Any] = {
        "id": tid,
        "case_id": case_id,
        "title": f"Tinjauan {label.lower()}: {case.get('title', vendor['name'])[:80]}",
        "status": "Baru",
        "sla": URGENCY_TO_SLA.get(label, "48h"),
        "assigned_unit": "Unit Pengawasan Vendor MBG",
        "escalation_level": label,
        "linked_vendor_id": vendor["id"],
        "linked_vendor_name": vendor["name"],
        "linked_region": case.get("region") or vendor.get("region", "-"),
        "priority": assess["final_priority_score"],
        "priority_label": label if priority_mode == "manual" else label,
        "priority_mode": priority_mode,
        "origin": origin,
        "recommended_action": assess.get("recommended_action", "Tinjau operator diperlukan."),
        "linked_evidence_ids": ev_ids,
        "audit_preview": auto_reason or "Tiket dibuat oleh operator.",
        "created_at": _now(),
        "updated_at": _now(),
    }
    if priority_mode == "suggested":
        ticket["suggested_priority"] = assess["final_priority_score"]
        ticket["suggested_priority_label"] = assess["priority_label"]
        ticket["priority_label"] = assess["priority_label"]
    if auto_reason:
        ticket["auto_ticket_reason"] = auto_reason
    sd.TICKETS.insert(0, ticket)
    sd.TICKET_BY_CASE[case_id] = ticket
    return ticket


def evaluate_signal(signal_id: int) -> dict[str, Any]:
    signal = get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail=f"Sinyal '{signal_id}' tidak ditemukan")
    if signal.get("case_id"):
        raise HTTPException(status_code=409, detail="Sinyal sudah terhubung ke kasus.")
    risk = score_signal(signal)
    eligible, reason = auto_ticket_gate.evaluate(signal, risk)
    return {"signal_id": signal_id, "risk": risk, "eligible_for_auto_ticket": eligible, "gate_reason": reason}


def create_auto_from_signal(signal_id: int) -> dict[str, Any]:
    preview = evaluate_signal(signal_id)
    if not preview["eligible_for_auto_ticket"]:
        return {**preview, "outcome": "skipped", "auto_ticket_created": False}

    signal = get_signal(signal_id)
    assert signal is not None
    risk = preview["risk"]
    vendor = sd.VENDOR_BY_ID["vnd-unknown"]
    cid = _next_case_id()
    region = signal.get("region") or UNKNOWN
    district = signal.get("district") or UNKNOWN
    school = signal.get("school") or UNKNOWN

    case = {
        "case_id": cid,
        "vendor_id": vendor["id"],
        "vendor_name_override": None,
        "vendor_source_note": None,
        "region": region,
        "district": district,
        "school": school,
        "issue_category": signal.get("issue_category") or "belum diklasifikasi",
        "priority_label": risk["priority_label"],
        "status": "Sedang Ditinjau",
        "title": f"Auto: {signal['summary'][:90]}",
        "assigned_investigator": None,
        "assigned_unit": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    sd.CASES.append(case)
    sd.CASE_BY_ID[cid] = case
    _register_risk(cid, vendor, risk, region=region)

    signal["case_id"] = cid
    signal["status"] = "Terhubung ke Kasus"
    ev = _add_evidence_from_signal(cid, signal)

    ticket = _build_ticket(
        cid, case, vendor, risk,
        origin="auto",
        priority_mode="suggested",
        auto_reason=preview["gate_reason"],
    )
    if ev:
        ticket["linked_evidence_ids"] = [ev["id"]]

    audit = [
        _add_audit(cid, "case_created", f"Kasus {sd.case_number(cid)} dibentuk otomatis dari sinyal #{signal_id}.", ticket["id"]),
        _add_audit(cid, "auto_ticket_created", f"Tiket {ticket['id']} dibuat otomatis. {preview['gate_reason']}", ticket["id"]),
    ]

    from app import demo_data
    from app.services.copilot.service import index_case_for_copilot
    index_case_for_copilot(cid)
    return {
        "outcome": "auto_created",
        "auto_ticket_created": True,
        "case_id": cid,
        "case_number": sd.case_number(cid),
        "ticket_id": ticket["id"],
        "risk": risk,
        "gate_reason": preview["gate_reason"],
        "audit_events": audit,
        "case": demo_data.case_detail(cid),
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }


def create_manual(
    case_id: str,
    *,
    auto_prioritize: bool = False,
    priority_label: str | None = None,
) -> dict[str, Any]:
    case = sd.CASE_BY_ID.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Kasus '{case_id}' tidak ditemukan")
    if sd.TICKET_BY_CASE.get(case_id):
        raise HTTPException(status_code=409, detail="Kasus sudah memiliki tiket aktif.")

    vendor = sd.VENDOR_BY_ID.get(case["vendor_id"], sd.VENDOR_BY_ID["vnd-unknown"])
    risk_existing = sd.RISK_BY_CASE.get(case_id)

    if auto_prioritize:
        from app.runtime_store import all_signals
        linked = [s for s in all_signals() if s.get("case_id") == case_id]
        if linked:
            assess = score_signal(linked[0])
        elif risk_existing:
            assess = {
                "final_priority_score": risk_existing["final_priority_score"],
                "priority_label": risk_existing["priority_label"],
                "severity_score": risk_existing["severity_score"],
                "confidence_score": risk_existing["confidence_score"],
                "actionability_score": risk_existing.get("actionability_score", 30),
                "recommended_action": risk_existing.get("recommended_action", "Tinjau operator."),
                "explanation": risk_existing.get("explanation", ""),
            }
        else:
            assess = score_signal({
                "source": "Formulir Publik",
                "source_confidence": 0.65,
                "urgency": case.get("priority_label", "Sedang"),
                "summary": case.get("title", ""),
                "text": case.get("title", ""),
                "issue_category": case.get("issue_category"),
                "region": case.get("region"),
                "school": case.get("school"),
            })
        mode = "suggested"
    else:
        if not priority_label:
            raise HTTPException(status_code=422, detail="priority_label wajib jika auto_prioritize=false")
        base_scores = {"Kritis": 88, "Tinggi": 78, "Sedang": 58, "Rendah": 38}
        score = base_scores.get(priority_label, 58)
        assess = {
            "final_priority_score": score,
            "priority_label": priority_label,
            "severity_score": score,
            "confidence_score": 50,
            "actionability_score": 30,
            "recommended_action": "Tindak lanjut sesuai prioritas operator.",
            "explanation": "Prioritas ditetapkan manual oleh operator.",
        }
        mode = "manual"

    ticket = _build_ticket(case_id, case, vendor, assess, origin="manual", priority_mode=mode)
    audit = _add_audit(case_id, "ticket_created", f"Tiket {ticket['id']} dibuat manual (mode: {mode}).", ticket["id"])

    from app import demo_data
    return {"ticket": ticket, "audit_event": audit, "case": demo_data.case_detail(case_id), "ai_notice": sd.GOVERNANCE_NOTICE}


def confirm_priority(ticket_id: str) -> dict[str, Any]:
    ticket = next((t for t in sd.TICKETS if t["id"] == ticket_id), None)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Tiket '{ticket_id}' tidak ditemukan")
    if ticket.get("priority_mode") != "suggested":
        raise HTTPException(status_code=409, detail="Tiket tidak dalam mode suggested.")
    ticket["priority_mode"] = "confirmed"
    ticket["priority"] = ticket.get("suggested_priority") or ticket["priority"]
    ticket["priority_label"] = ticket.get("suggested_priority_label") or ticket.get("escalation_level")
    ticket["escalation_level"] = ticket["priority_label"]
    ticket["updated_at"] = _now()
    audit = _add_audit(ticket["case_id"], "priority_confirmed", f"Operator mengonfirmasi prioritas suggested: {ticket['priority_label']} ({ticket['priority']}).", ticket_id)
    return {"ticket": ticket, "audit_event": audit, "ai_notice": sd.GOVERNANCE_NOTICE}
