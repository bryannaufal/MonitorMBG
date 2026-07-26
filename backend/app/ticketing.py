"""Ticketing domain rules: SLA, ownership, and the status lifecycle.

One module so every writer (case API, ticket API, seed loader) resolves a
ticket the same way.  Before this existed each caller invented its own
defaults, which is how a `Kritis` case ended up with a 72h child ticket: the
create endpoint carried a literal ``sla = "72h"`` and never read the parent.

Vocabulary: a **ticket** is the child work item.  ``workstream`` is only a
label on it grouping related tickets under one case.  The parent **case** owns
the lifecycle; ticket status never closes a case.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

# ── SLA policy ───────────────────────────────────────────────────────────
# Severity is the primary driver; urgency/impact adjust within the band.
# Named policies rather than bare hour counts so the UI and the audit trail
# can state *which* rule applied, not just the resulting number.
SLA_POLICIES: dict[str, dict[str, Any]] = {
    "P1": {"hours": 4, "label": "4h", "description": "Kritis — respons darurat"},
    "P2": {"hours": 24, "label": "24h", "description": "Tinggi — prioritas tinggi"},
    "P3": {"hours": 48, "label": "48h", "description": "Sedang — penanganan standar"},
    "P4": {"hours": 72, "label": "72h", "description": "Rendah — pemantauan rutin"},
}

# Severity -> base policy.  Both Indonesian and English labels map, because
# seed data uses "Kritis" while some frontend snapshots carry "Critical".
SEVERITY_POLICY = {
    "kritis": "P1", "critical": "P1",
    "tinggi": "P2", "high": "P2",
    "sedang": "P3", "medium": "P3",
    "rendah": "P4", "low": "P4",
}

# Severity -> escalation band and the numeric priority used for queue sorting.
SEVERITY_PRIORITY = {"P1": 95, "P2": 78, "P3": 55, "P4": 30}
SEVERITY_CANONICAL = {"P1": "Kritis", "P2": "Tinggi", "P3": "Sedang", "P4": "Rendah"}

IMPACT_LEVELS = ("Luas", "Sedang", "Terbatas")
URGENCY_LEVELS = ("Segera", "Normal", "Terjadwal")

DEFAULT_IMPACT = "Sedang"
DEFAULT_URGENCY = "Normal"
UNASSIGNED = "Belum ditetapkan"

# At-risk threshold: a ticket enters "at risk" once this share of its SLA
# window has elapsed without resolution.
AT_RISK_RATIO = 0.75


def policy_for(severity: str | None, impact: str | None = None,
               urgency: str | None = None) -> str:
    """Resolve the SLA policy code from severity, nudged by impact/urgency.

    Severity sets the band.  ``Segera`` urgency or ``Luas`` impact pulls one
    band tighter; ``Terjadwal`` urgency with ``Terbatas`` impact relaxes one
    band.  A `Kritis` ticket can never relax below P2 — the escalation floor
    is what the old flat 72h default was missing.
    """
    code = SEVERITY_POLICY.get((severity or "").strip().lower(), "P3")
    if code == "P1":
        # Kritis never relaxes out of the top band, whatever impact/urgency say.
        return "P1"
    rank = int(code[1])
    if (urgency or "") == "Segera" or (impact or "") == "Luas":
        rank -= 1
    elif (urgency or "") == "Terjadwal" and (impact or "") == "Terbatas":
        rank += 1
    return f"P{min(4, max(1, rank))}"


def sla_label(policy_code: str) -> str:
    return SLA_POLICIES[policy_code]["label"]


def sla_hours(policy_code: str) -> int:
    return SLA_POLICIES[policy_code]["hours"]


def hours_from_label(label: str | None) -> int | None:
    """Parse a legacy ``"72h"`` SLA string back into hours.

    Pre-existing tickets stored SLA as a display string with no due date; this
    is how they are migrated onto the timestamp-based engine without guessing.
    """
    text = (label or "").strip().lower().removesuffix("h")
    return int(text) if text.isdigit() else None


def due_at(started: datetime | str, policy_code: str) -> str:
    start = datetime.fromisoformat(started) if isinstance(started, str) else started
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    return (start + timedelta(hours=sla_hours(policy_code))).isoformat()


# ── Status lifecycle ─────────────────────────────────────────────────────
# Grouped by meaning so monitoring can ask "is this ticket active?" without
# hardcoding a status list at every call site.
OPEN_STATUSES = {"Baru"}
IN_PROGRESS_STATUSES = {"Sedang Ditinjau", "Verifikasi Lapangan"}
# Waiting states stop the SLA clock: the delay is not the operator's.
WAITING_STATUSES = {"Menunggu Klarifikasi Vendor", "Ditahan / On Hold"}
RESOLVED_STATUSES = {"Selesai"}
CLOSED_STATUSES = {"Ditutup", "Dibatalkan"}

TICKET_STATUSES = (
    OPEN_STATUSES | IN_PROGRESS_STATUSES | WAITING_STATUSES
    | RESOLVED_STATUSES | CLOSED_STATUSES
)

# Terminal statuses stop SLA evaluation entirely.
TERMINAL_STATUSES = RESOLVED_STATUSES | CLOSED_STATUSES

# Allowed transitions.  Deliberately permissive within the active states
# (operators reroute work constantly) but strict about terminal ones: a closed
# or cancelled ticket must be reopened explicitly, never silently edited.
TRANSITIONS: dict[str, set[str]] = {
    "Baru": {"Sedang Ditinjau", "Verifikasi Lapangan", "Menunggu Klarifikasi Vendor",
             "Ditahan / On Hold", "Dibatalkan"},
    "Sedang Ditinjau": {"Verifikasi Lapangan", "Menunggu Klarifikasi Vendor",
                        "Ditahan / On Hold", "Selesai", "Dibatalkan"},
    "Verifikasi Lapangan": {"Sedang Ditinjau", "Menunggu Klarifikasi Vendor",
                            "Ditahan / On Hold", "Selesai", "Dibatalkan"},
    "Menunggu Klarifikasi Vendor": {"Sedang Ditinjau", "Verifikasi Lapangan",
                                    "Ditahan / On Hold", "Selesai", "Dibatalkan"},
    "Ditahan / On Hold": {"Sedang Ditinjau", "Verifikasi Lapangan",
                          "Menunggu Klarifikasi Vendor", "Dibatalkan"},
    "Selesai": {"Ditutup", "Sedang Ditinjau"},  # reopen for rework
    "Ditutup": {"Sedang Ditinjau"},             # explicit reopen only
    "Dibatalkan": set(),
}


def can_transition(current: str, target: str) -> bool:
    if current == target:
        return True
    return target in TRANSITIONS.get(current, set())


# ── SLA evaluation ───────────────────────────────────────────────────────
def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def sla_state(ticket: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Derive the live SLA indicator for one ticket.

    Returns ``sla_state`` (on_track | at_risk | overdue | met | breached |
    paused | unknown) plus the hours remaining.  Computed on read rather than
    stored, so a ticket cannot drift out of sync with the wall clock.
    """
    now = now or datetime.now(timezone.utc)
    status = ticket.get("status") or ""
    deadline = _parse(ticket.get("due_at"))

    if deadline is None:
        return {"sla_state": "unknown", "hours_remaining": None, "overdue": False,
                "at_risk": False, "breached": False}

    resolved_at = _parse(ticket.get("resolved_at"))
    if status in TERMINAL_STATUSES:
        # Completed work is judged against when it finished, not "now".
        finished = resolved_at or _parse(ticket.get("updated_at")) or now
        breached = finished > deadline
        return {"sla_state": "breached" if breached else "met",
                "hours_remaining": round((deadline - finished).total_seconds() / 3600, 1),
                "overdue": False, "at_risk": False, "breached": breached}

    if status in WAITING_STATUSES:
        # Clock paused: waiting on an external party is not an SLA breach.
        return {"sla_state": "paused",
                "hours_remaining": round((deadline - now).total_seconds() / 3600, 1),
                "overdue": False, "at_risk": False, "breached": False}

    remaining = (deadline - now).total_seconds() / 3600
    if remaining <= 0:
        return {"sla_state": "overdue", "hours_remaining": round(remaining, 1),
                "overdue": True, "at_risk": False, "breached": True}

    total = sla_hours(ticket.get("sla_policy") or "P3")
    elapsed_ratio = 1 - (remaining / total) if total else 0
    at_risk = elapsed_ratio >= AT_RISK_RATIO
    return {"sla_state": "at_risk" if at_risk else "on_track",
            "hours_remaining": round(remaining, 1), "overdue": False,
            "at_risk": at_risk, "breached": False}


def enrich(ticket: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    """Ticket dict plus its derived SLA indicators, for API responses."""
    return {**ticket, **sla_state(ticket, now)}


def summarise(tickets: list[dict[str, Any]], now: datetime | None = None) -> dict[str, int]:
    """Monitoring counters over a ticket collection.

    Single source of truth for both the case workspace and the ticket board so
    the two views can never disagree.  Counters are independent facets, not a
    partition: a ticket is counted in every bucket it belongs to.
    """
    states = [sla_state(t, now) for t in tickets]
    return {
        "total": len(tickets),
        "open": len([t for t in tickets if t.get("status") in OPEN_STATUSES]),
        "in_progress": len([t for t in tickets if t.get("status") in IN_PROGRESS_STATUSES]),
        "waiting": len([t for t in tickets if t.get("status") in WAITING_STATUSES]),
        "resolved": len([t for t in tickets if t.get("status") in RESOLVED_STATUSES]),
        "closed": len([t for t in tickets if t.get("status") in CLOSED_STATUSES]),
        "completed": len([t for t in tickets if t.get("status") in TERMINAL_STATUSES]),
        "on_track": len([s for s in states if s["sla_state"] == "on_track"]),
        "at_risk": len([s for s in states if s["at_risk"]]),
        "overdue": len([s for s in states if s["overdue"]]),
        "paused": len([s for s in states if s["sla_state"] == "paused"]),
        "met_sla": len([s for s in states if s["sla_state"] == "met"]),
        "breached_sla": len([s for s in states if s["sla_state"] == "breached"]),
        "unassigned": len([t for t in tickets if not (t.get("assignee") or "").strip()]),
    }


# ── Assignment ───────────────────────────────────────────────────────────
def resolve_assignment(case: dict[str, Any], assignee: str | None,
                       assignment_group: str | None) -> tuple[str | None, str, str]:
    """Resolve ticket ownership, returning (assignee, group, rule applied).

    Explicit input wins.  Otherwise the ticket inherits the parent case's
    owner/team — the rule is stated in the returned string so the audit trail
    records *why* a ticket landed where it did instead of it looking manual.
    """
    if assignee and assignment_group:
        return assignee, assignment_group, "explicit"
    if assignee:
        group = (assignment_group or case.get("handling_team")
                 or case.get("assigned_unit") or UNASSIGNED)
        return assignee, group, "assignee_explicit_group_inherited"
    if assignment_group:
        return None, assignment_group, "group_explicit_pending_individual"
    group = case.get("handling_team") or case.get("assigned_unit")
    owner = case.get("primary_owner") or case.get("assigned_investigator")
    if owner or group:
        return owner, group or UNASSIGNED, "inherited_from_case"
    return None, UNASSIGNED, "unassigned_needs_triage"


def resolve_severity(case: dict[str, Any], override: str | None) -> tuple[str, str]:
    """Child severity: explicit override, else inherited from the parent case.

    Returns (severity, rule).  Inheritance is the default precisely because
    the old code inherited *nothing* and fell back to a flat default.
    """
    if override:
        return override, "override"
    inherited = case.get("severity") or case.get("priority_label")
    if inherited:
        return inherited, "inherited_from_case"
    return "Sedang", "default_no_parent_severity"
