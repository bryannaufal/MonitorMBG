"""Case-centered oversight API.

Cases are the monitored aggregate.  Ticket mutations are deliberately kept
separate from case lifecycle transitions: closing work items alone never closes
a case.
"""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app import demo_data, persistence, seed_data as sd, ticketing

router = APIRouter()

CASE_STATUSES = {
    "Open & Monitored", "Assessing", "In Handling", "Pending / Blocked",
    "Escalated", "Resolved – Pending Verification", "Closed", "Reopened", "Merged / Invalid",
}


class CaseUpdate(BaseModel):
    status: str | None = None
    primary_owner: str | None = None
    handling_team: str | None = None
    severity: str | None = None
    handling_strategy: Literal["direct", "single_ticket", "multi_ticket"] | None = None
    blocker: str | None = None
    clear_blocker: str | None = None
    progress_note: str | None = None
    resolution_summary: str | None = None
    actor: str = "Demo Operator"


class ChildTicketCreate(BaseModel):
    """Child ticket intake.

    Every operational field is optional *except* the title: anything left
    unset is resolved by an explicit rule in ``app.ticketing`` (severity
    inherited from the parent case, SLA derived from that severity, ownership
    inherited from the case team) and the rule applied is written to the audit
    trail.  Nothing silently defaults to a fixed value.
    """

    title: str
    description: str | None = None
    severity: str | None = None
    impact: str | None = None
    urgency: str | None = None
    sla_policy: str | None = None
    due_at: str | None = None
    assignee: str | None = None
    assignment_group: str | None = None
    assigned_unit: str | None = None  # legacy alias for assignment_group
    workstream: str | None = None
    category: str | None = None
    labels: list[str] = []
    notes: str | None = None
    priority: int | None = None
    recommended_action: str | None = None
    actor: str = "Demo Operator"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit(case_id: str, event_type: str, description: str, actor: str, ticket_id: str | None = None) -> dict:
    event = {
        "id": max((item["id"] for item in sd.AUDIT), default=0) + 1,
        "case_id": case_id, "ticket_id": ticket_id, "event_type": event_type,
        "actor": actor, "role": "Operator Distrik", "description": description, "timestamp": _now(),
    }
    sd.AUDIT.insert(0, event)
    persistence.persist("audit", event)
    return event


@router.get("")
@router.get("/")
async def list_cases(
    priority: str | None = Query(default=None),
    status: str | None = Query(default=None),
    region: str | None = Query(default=None),
    issue: str | None = Query(default=None),
    search: str | None = Query(default=None),
):
    """List case work queue with optional operator filters."""
    items = demo_data.oversight_cases()

    if priority:
        items = [item for item in items if item["priority_label"].lower() == priority.lower()]
    if status:
        items = [item for item in items if status.lower() in item["status"].lower()]
    if region:
        items = [item for item in items if region.lower() in item["region"].lower()]
    if issue:
        items = [item for item in items if issue.lower() in item["issue_category"].lower()]
    if search:
        query = search.lower()
        items = [
            item
            for item in items
            if query in item["title"].lower()
            or query in item["vendor_name"].lower()
            or query in item["school"].lower()
            or query in item["case_id"].lower()
        ]

    return {"items": items, "total": len(items)}


@router.get("/{case_id}")
async def get_case(case_id: str):
    """Get the full investigation hub for one oversight case."""
    return demo_data.case_detail(case_id)


@router.patch("/{case_id}")
async def update_case(case_id: str, update: CaseUpdate):
    """Record a case-level handling update without inferring it from tickets."""
    case = sd.CASE_BY_ID.get(case_id)
    if not case:
        return demo_data.case_detail(case_id)  # raises the standard explicit 404
    events: list[dict] = []
    if update.status:
        if update.status not in CASE_STATUSES:
            raise HTTPException(status_code=422, detail="Status kasus tidak didukung.")
        if update.status == "Closed" and not (update.resolution_summary or case.get("resolution_summary")):
            raise HTTPException(status_code=422, detail="Penutupan kasus memerlukan ringkasan resolusi terverifikasi.")
        before = case.get("status", "Open & Monitored")
        case["status"] = update.status
        events.append(_audit(case_id, "case_status_changed", f"Status kasus diubah dari {before} menjadi {update.status}.", update.actor))
    for field, label in (("primary_owner", "Pemilik utama"), ("handling_team", "Tim penanganan"), ("severity", "Keparahan"), ("handling_strategy", "Strategi penanganan")):
        value = getattr(update, field)
        if value is not None and value != case.get(field):
            before = case.get(field) or "Belum ditetapkan"
            case[field] = value
            # Keep old consumers functioning while they migrate.
            if field == "primary_owner": case["assigned_investigator"] = value
            if field == "handling_team": case["assigned_unit"] = value
            events.append(_audit(case_id, f"{field}_changed", f"{label} diubah dari {before} menjadi {value}.", update.actor))
    blockers = list(case.get("blockers") or [])
    if update.blocker and update.blocker not in blockers:
        blockers.append(update.blocker)
        case["blockers"] = blockers
        events.append(_audit(case_id, "blocker_added", f"Hambatan ditambahkan: {update.blocker}.", update.actor))
    if update.clear_blocker and update.clear_blocker in blockers:
        blockers.remove(update.clear_blocker)
        case["blockers"] = blockers
        events.append(_audit(case_id, "blocker_removed", f"Hambatan diselesaikan: {update.clear_blocker}.", update.actor))
    if update.progress_note:
        events.append(_audit(case_id, "handling_update", update.progress_note, update.actor))
    if update.resolution_summary:
        case["resolution_summary"] = update.resolution_summary
        events.append(_audit(case_id, "resolution_updated", update.resolution_summary, update.actor))
    case["updated_at"] = _now()
    persistence.persist("case", case)
    return {"case": demo_data.case_detail(case_id), "audit_events": events, "ai_notice": demo_data.DEMO_NOTICE}


@router.post("/{case_id}/tickets")
async def create_child_ticket(case_id: str, body: ChildTicketCreate):
    """Create an optional child workstream under an existing case."""
    case = sd.CASE_BY_ID.get(case_id)
    if not case:
        return demo_data.case_detail(case_id)
    number = max((int("".join(ch for ch in item["id"] if ch.isdigit()) or 0) for item in demo_data.TICKETS), default=0) + 1
    vendor = sd.VENDOR_BY_ID[case["vendor_id"]]
    now = _now()

    # Severity first: the SLA is derived from it, so an inherited `Kritis`
    # parent yields a P1 child rather than the old flat 72h default.
    severity, severity_rule = ticketing.resolve_severity(case, body.severity)
    impact = body.impact or ticketing.DEFAULT_IMPACT
    urgency = body.urgency or ticketing.DEFAULT_URGENCY
    if body.sla_policy:
        if body.sla_policy not in ticketing.SLA_POLICIES:
            raise HTTPException(status_code=422, detail=f"Kebijakan SLA '{body.sla_policy}' tidak dikenal.")
        policy, sla_rule = body.sla_policy, "explicit_policy"
    else:
        policy = ticketing.policy_for(severity, impact, urgency)
        sla_rule = f"derived_from_severity:{severity}"
    assignee, group, assign_rule = ticketing.resolve_assignment(
        case, body.assignee, body.assignment_group or body.assigned_unit)

    ticket = {
        "id": f"TKT-{number:03d}", "case_id": case_id, "title": body.title,
        "description": body.description, "status": "Baru",
        "severity": severity, "impact": impact, "urgency": urgency,
        "sla_policy": policy, "sla": ticketing.sla_label(policy),
        "due_at": body.due_at or ticketing.due_at(now, policy),
        "assignee": assignee, "assignment_group": group,
        "assigned_unit": group,  # legacy alias kept in sync
        "escalation_level": severity,
        "linked_vendor_id": vendor["id"], "linked_vendor_name": vendor["name"],
        "linked_region": case.get("region") or vendor["region"],
        "priority": body.priority if body.priority is not None
        else ticketing.SEVERITY_PRIORITY[ticketing.policy_for(severity)],
        "category": body.category or case.get("issue_category"),
        "labels": body.labels,
        "notes": [{"actor": body.actor, "note": body.notes, "at": now}] if body.notes else [],
        "recommended_action": body.recommended_action or "Tindak lanjuti workstream dan laporkan progres ke kasus.",
        "linked_evidence_ids": [], "audit_preview": "Tiket anak dibuat dari workspace kasus.",
        "workstream": body.workstream or "Tindak lanjut",
        "resolved_at": None, "created_at": now, "updated_at": now,
    }
    demo_data.TICKETS.append(ticket)
    sd.TICKET_BY_CASE.setdefault(case_id, ticket)
    persistence.persist("ticket", ticket)
    if case.get("handling_strategy") == "direct": case["handling_strategy"] = "single_ticket"
    elif len([t for t in demo_data.TICKETS if t["case_id"] == case_id]) > 1: case["handling_strategy"] = "multi_ticket"
    case["updated_at"] = now
    persistence.persist("case", case)
    # The defaulting rules are recorded, not just their results, so an operator
    # can see why a ticket got its SLA and owner.
    event = _audit(
        case_id, "child_ticket_created",
        f"Workstream '{ticket['workstream']}' dibuat sebagai tiket {ticket['id']}. "
        f"Keparahan {severity} ({severity_rule}), SLA {ticket['sla']} / {policy} ({sla_rule}), "
        f"pemilik {assignee or ticketing.UNASSIGNED} · {group} ({assign_rule}).",
        body.actor, ticket["id"])
    return {"ticket": ticketing.enrich(ticket), "case": demo_data.case_detail(case_id),
            "applied_rules": {"severity": severity_rule, "sla": sla_rule, "assignment": assign_rule},
            "audit_event": event, "ai_notice": demo_data.DEMO_NOTICE}
