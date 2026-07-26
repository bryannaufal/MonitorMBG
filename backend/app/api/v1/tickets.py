"""Child-ticket execution API.

Ticket status is visible in the parent case timeline but never changes the
parent case lifecycle automatically.  All SLA/ownership rules live in
``app.ticketing`` so this layer only validates input and records audit events.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app import demo_data, persistence, ticketing

router = APIRouter()


class TicketStatusUpdate(BaseModel):
    status: str
    actor: str = "Demo Operator"
    note: str | None = None


class TicketUpdate(BaseModel):
    """Partial update of a ticket's operational attributes.

    Changing severity recalculates the SLA policy and due date unless the
    caller pins one explicitly — the recalculation is the point, since a
    ticket escalated to `Kritis` must not keep a 72h deadline.
    """

    title: str | None = None
    description: str | None = None
    status: str | None = None
    severity: str | None = None
    impact: str | None = None
    urgency: str | None = None
    sla_policy: str | None = None
    due_at: str | None = None
    assignee: str | None = None
    assignment_group: str | None = None
    workstream: str | None = None
    category: str | None = None
    labels: list[str] | None = None
    priority: int | None = None
    recommended_action: str | None = None
    note: str | None = None
    reassign_reason: str | None = None
    actor: str = "Demo Operator"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit(ticket: dict, event_type: str, description: str, actor: str) -> dict:
    event = {
        # Highest existing id + 1: len() collides once any row is deleted.
        "id": max((a["id"] for a in demo_data.AUDIT_TRAIL), default=0) + 1,
        "case_id": ticket["case_id"],
        "ticket_id": ticket["id"],
        "event_type": event_type,
        "actor": actor,
        "role": "District Operator",
        "description": description,
        "timestamp": _now(),
    }
    demo_data.AUDIT_TRAIL.insert(0, event)
    persistence.persist("audit", event)
    return event


def _apply_status(ticket: dict, target: str, actor: str, note: str | None) -> dict:
    """Validate and apply a lifecycle transition, returning the audit event."""
    if target not in ticketing.TICKET_STATUSES:
        raise HTTPException(status_code=422, detail=f"Status tiket '{target}' tidak dikenal.")
    current = ticket.get("status") or "Baru"
    if not ticketing.can_transition(current, target):
        raise HTTPException(
            status_code=422,
            detail=f"Transisi status '{current}' → '{target}' tidak diizinkan.")
    ticket["status"] = target
    # Resolution time is stamped once, so SLA compliance is judged against when
    # the work actually finished rather than the latest edit.
    if target in ticketing.TERMINAL_STATUSES and not ticket.get("resolved_at"):
        ticket["resolved_at"] = _now()
    elif target not in ticketing.TERMINAL_STATUSES:
        ticket["resolved_at"] = None
    return _audit(
        ticket, "child_ticket_status_changed",
        note or (f"Status workstream tiket {ticket['id']} diubah dari {current} menjadi {target}. "
                 f"Status kasus tidak diubah otomatis."),
        actor)


@router.get("")
@router.get("/")
async def list_tickets(
    status: str | None = Query(default=None),
    sla_state: str | None = Query(default=None),
    assignee: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    unassigned: bool | None = Query(default=None),
):
    """List the ticket queue with live SLA indicators and monitoring counters."""
    items = [ticketing.enrich(t) for t in demo_data.TICKETS]
    if status:
        items = [t for t in items if t.get("status") == status]
    if sla_state:
        items = [t for t in items if t.get("sla_state") == sla_state]
    if assignee:
        items = [t for t in items if (t.get("assignee") or "") == assignee]
    if case_id:
        items = [t for t in items if t.get("case_id") == case_id]
    if unassigned:
        items = [t for t in items if not (t.get("assignee") or "").strip()]
    # Overdue first, then by priority: the queue should surface what is late.
    items.sort(key=lambda t: (not t.get("overdue"), -(t.get("priority") or 0)))
    return {"items": items, "total": len(items),
            "summary": ticketing.summarise(demo_data.TICKETS),
            "sla_policies": ticketing.SLA_POLICIES,
            "statuses": sorted(ticketing.TICKET_STATUSES)}


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a single ticket with its derived SLA state."""
    return ticketing.enrich(demo_data.get_or_404(demo_data.TICKETS, ticket_id, "Ticket"))


@router.patch("/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, update: TicketStatusUpdate):
    """Move a ticket through its lifecycle (kept for the board's quick action)."""
    ticket = demo_data.get_or_404(demo_data.TICKETS, ticket_id, "Ticket")
    event = _apply_status(ticket, update.status, update.actor, update.note)
    ticket["updated_at"] = _now()
    persistence.persist("ticket", ticket)
    return {"ticket": ticketing.enrich(ticket), "audit_event": event,
            "ai_notice": demo_data.DEMO_NOTICE}


@router.patch("/{ticket_id}")
async def update_ticket(ticket_id: str, update: TicketUpdate):
    """Update ticket attributes, recalculating the SLA when severity changes."""
    ticket = demo_data.get_or_404(demo_data.TICKETS, ticket_id, "Ticket")
    events: list[dict] = []

    if update.status:
        events.append(_apply_status(ticket, update.status, update.actor, update.note))

    # Reassignment is recorded with both endpoints of the move so ownership
    # history is reconstructable from the audit trail alone.
    if update.assignee is not None and update.assignee != ticket.get("assignee"):
        before = ticket.get("assignee") or ticketing.UNASSIGNED
        ticket["assignee"] = update.assignee or None
        events.append(_audit(
            ticket, "ticket_reassigned",
            f"Penanggung jawab tiket {ticket['id']} diubah dari {before} menjadi "
            f"{update.assignee or ticketing.UNASSIGNED}."
            + (f" Alasan: {update.reassign_reason}." if update.reassign_reason else ""),
            update.actor))
    if update.assignment_group is not None and update.assignment_group != ticket.get("assignment_group"):
        before = ticket.get("assignment_group") or ticketing.UNASSIGNED
        ticket["assignment_group"] = update.assignment_group
        ticket["assigned_unit"] = update.assignment_group  # legacy alias
        events.append(_audit(
            ticket, "ticket_group_reassigned",
            f"Grup penanganan tiket {ticket['id']} diubah dari {before} menjadi {update.assignment_group}.",
            update.actor))

    severity_changed = update.severity is not None and update.severity != ticket.get("severity")
    if severity_changed:
        before = ticket.get("severity") or "-"
        ticket["severity"] = update.severity
        ticket["escalation_level"] = update.severity
        events.append(_audit(
            ticket, "ticket_severity_changed",
            f"Keparahan tiket {ticket['id']} diubah dari {before} menjadi {update.severity}.",
            update.actor))
    for field in ("impact", "urgency"):
        value = getattr(update, field)
        if value is not None and value != ticket.get(field):
            ticket[field] = value
            severity_changed = True  # impact/urgency also shift the SLA band

    # Explicit policy/due date always wins; otherwise a severity/impact/urgency
    # change re-derives both from the current attributes.
    if update.sla_policy:
        if update.sla_policy not in ticketing.SLA_POLICIES:
            raise HTTPException(status_code=422, detail=f"Kebijakan SLA '{update.sla_policy}' tidak dikenal.")
        _set_policy(ticket, update.sla_policy, events, update.actor, "ditetapkan manual")
    elif severity_changed:
        policy = ticketing.policy_for(ticket.get("severity"), ticket.get("impact"), ticket.get("urgency"))
        if policy != ticket.get("sla_policy"):
            _set_policy(ticket, policy, events, update.actor,
                        f"dihitung ulang dari keparahan {ticket.get('severity')}")
    if update.due_at:
        before = ticket.get("due_at")
        ticket["due_at"] = update.due_at
        events.append(_audit(
            ticket, "ticket_due_date_changed",
            f"Target penyelesaian tiket {ticket['id']} diubah dari {before or '-'} menjadi {update.due_at}.",
            update.actor))

    for field in ("title", "description", "workstream", "category", "labels",
                  "priority", "recommended_action"):
        value = getattr(update, field)
        if value is not None and value != ticket.get(field):
            ticket[field] = value
            events.append(_audit(ticket, "ticket_updated",
                                 f"Field '{field}' tiket {ticket['id']} diperbarui.", update.actor))

    if update.note and not update.status:
        # A note without a status change is a standalone progress entry.
        ticket.setdefault("notes", []).append(
            {"actor": update.actor, "note": update.note, "at": _now()})
        events.append(_audit(ticket, "ticket_progress_note", update.note, update.actor))

    ticket["updated_at"] = _now()
    persistence.persist("ticket", ticket)
    return {"ticket": ticketing.enrich(ticket), "audit_events": events,
            "case": demo_data.case_detail(ticket["case_id"]),
            "ai_notice": demo_data.DEMO_NOTICE}


def _set_policy(ticket: dict, policy: str, events: list[dict], actor: str, reason: str) -> None:
    """Apply an SLA policy and slide the due date off the ticket's start."""
    before = ticket.get("sla") or "-"
    ticket["sla_policy"] = policy
    ticket["sla"] = ticketing.sla_label(policy)
    ticket["due_at"] = ticketing.due_at(ticket.get("created_at") or _now(), policy)
    events.append(_audit(
        ticket, "ticket_sla_changed",
        f"SLA tiket {ticket['id']} diubah dari {before} menjadi {ticket['sla']} ({policy}); {reason}. "
        f"Target penyelesaian {ticket['due_at']}.",
        actor))


@router.get("/{ticket_id}/audit")
async def ticket_audit(ticket_id: str):
    """Activity log for one ticket."""
    demo_data.get_or_404(demo_data.TICKETS, ticket_id, "Ticket")
    events = [a for a in demo_data.AUDIT_TRAIL if a.get("ticket_id") == ticket_id]
    return {"items": events, "total": len(events)}
