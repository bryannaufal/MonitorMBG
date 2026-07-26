"""Write-through persistence for the runtime oversight state.

The API layer keeps its dict-shaped domain objects (``seed_data.CASES`` and
friends) because the response contract and the frontend types are built on
them.  This module makes those dicts *durable*:

- :func:`hydrate` loads the DB into the ``seed_data`` collections at startup,
  replacing the module-level seed literals as the source of truth.
- :func:`persist` writes a mutated dict back to its table.

So reads stay synchronous and cheap (no async fan-out through eleven
endpoints), while every operator mutation survives a restart.  Each ``persist``
call is one short transaction; there is no unit-of-work spanning a request.

Failure policy: writes are best-effort and never break the demo.  A dead DB
downgrades the app to the old in-memory behaviour with a logged warning rather
than 500-ing an operator mid-review.

ponytail: sync engine + per-call transaction. Batch into a request-scoped
unit-of-work if write volume ever makes the round-trips visible.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from app import seed_data as sd, ticketing
from app.config import settings
from app.models.oversight import (
    AuditEvent,
    Case,
    Evidence,
    RiskAssessment,
    Signal,
    Ticket,
    Vendor,
)

log = logging.getLogger(__name__)

# The app's async URL drives the API; persistence uses the sync driver so a
# write can be issued from the existing synchronous store functions.
# psycopg (v3) serves both sync and async, so the same package covers both.
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg")

_engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=_engine, expire_on_commit=False, future=True)

# Set once hydrate() confirms the DB is reachable and populated.  While False
# every persist() is a no-op and the app behaves exactly as the old demo build.
_enabled = False


def enabled() -> bool:
    return _enabled


def _dt(value: Any) -> datetime | None:
    """Domain dicts carry ISO strings; columns want datetimes."""
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _iso(value: Any) -> Any:
    """Columns hand back datetimes; the API contract is ISO strings."""
    return value.isoformat() if isinstance(value, datetime) else value


# ── Row -> domain dict ───────────────────────────────────────────────────
# Only fields the API actually reads are mapped back; the dict shape must stay
# identical to the seed literals or _build_case() starts seeing None.

def _case_dict(row: Case) -> dict[str, Any]:
    return {
        "case_id": row.case_id,
        "vendor_id": row.vendor_id,
        "school": row.school,
        "region": row.region,
        "district": row.district,
        "vendor_name_override": row.vendor_name_override,
        "vendor_source_note": row.vendor_source_note,
        "issue_category": row.issue_category,
        "priority_label": row.priority_label,
        "severity": row.severity or row.priority_label,
        "status": row.status,
        "title": row.title,
        "assigned_investigator": row.assigned_investigator,
        "assigned_unit": row.assigned_unit,
        "case_type": row.case_type,
        "case_subtype": row.case_subtype,
        "impact_summary": row.impact_summary,
        "primary_owner": row.primary_owner,
        "handling_team": row.handling_team,
        "secondary_owner": row.secondary_owner,
        "watchers": row.watchers or [],
        "due_at": _iso(row.due_at),
        "handling_strategy": row.handling_strategy,
        "related_case_id": row.related_case_id,
        "case_relationship": row.case_relationship,
        "blockers": row.blockers or [],
        "resolution_summary": row.resolution_summary,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _signal_dict(row: Signal) -> dict[str, Any]:
    return {
        "id": row.id,
        "case_id": row.case_id,
        "source": row.source,
        "source_confidence": row.source_confidence,
        "urgency": row.urgency,
        "status": row.status,
        "summary": row.summary,
        "text": row.text,
        "vendor_id": row.vendor_id,
        "vendor_name": row.vendor_name,
        "region": row.region,
        "district": row.district,
        "school": row.school,
        "issue_category": row.issue_category,
        "attachment_path": row.attachment_path,
        "attachment_title": row.attachment_title,
        "attachment_source": row.attachment_source,
        "attachment_note": row.attachment_note,
        "reviewer_note": row.reviewer_note,
        "created_at": _iso(row.created_at),
        # Asal intake tidak punya kolom sendiri; diturunkan dari sumber sinyal
        # agar badge asal tetap tampil setelah data melewati database.
        **({"intake_origin": "scraper_twitter"} if row.source == "Media Sosial" else {}),
    }


def _evidence_dict(row: Evidence) -> dict[str, Any]:
    return {
        "id": row.id,
        "case_id": row.case_id,
        "signal_id": row.signal_id,
        "type": row.type,
        "title": row.title,
        "file_path": row.file_path,
        "linked_entity": row.linked_entity,
        "source": row.source,
        "ocr_result": row.ocr_result,
        "image_text_match_score": row.image_text_match_score,
        "duplicate_score": row.duplicate_score,
        "confidence_score": row.confidence_score,
        "review_status": row.review_status,
        "reviewer_note": row.reviewer_note,
        "unlinked_from_case": row.unlinked_from_case,
        "created_at": _iso(row.created_at),
    }


def _risk_dict(row: RiskAssessment) -> dict[str, Any]:
    return {
        "id": row.id,
        "case_id": row.case_id,
        "vendor_id": row.vendor_id,
        "vendor_name": row.vendor_name,
        "region": row.region,
        "severity_score": row.severity_score,
        "confidence_score": row.confidence_score,
        "nutrition_concern_score": row.nutrition_concern_score,
        "cost_anomaly_score": row.cost_anomaly_score,
        "anomaly_score": row.anomaly_score,
        "final_priority_score": row.final_priority_score,
        "priority_label": row.priority_label,
        "explanation": row.explanation,
        "recommended_action": row.recommended_action,
        "computed_at": _iso(row.computed_at),
        "ai_notice": sd.GOVERNANCE_NOTICE,
    }


def _ticket_dict(row: Ticket) -> dict[str, Any]:
    # Legacy rows predate the SLA engine: they carry an ``sla`` label but no
    # policy or due date.  Backfill both on read so an old ticket still gets a
    # real SLA state instead of silently reading as "unknown" forever.
    policy = row.sla_policy
    if not policy:
        hours = ticketing.hours_from_label(row.sla)
        policy = next((code for code, spec in ticketing.SLA_POLICIES.items()
                       if spec["hours"] == hours), None)
        if policy is None:
            policy = ticketing.policy_for(row.severity or row.escalation_level)
    return {
        "id": row.id,
        "case_id": row.case_id,
        "title": row.title,
        "description": row.description,
        "status": row.status,
        "severity": row.severity or row.escalation_level or None,
        "impact": row.impact,
        "urgency": row.urgency,
        "sla_policy": policy,
        "sla": row.sla or ticketing.sla_label(policy),
        "assignee": row.assignee,
        "assignment_group": row.assignment_group or row.assigned_unit,
        "assigned_unit": row.assigned_unit,
        "category": row.category,
        "labels": row.labels or [],
        "notes": row.notes or [],
        "resolved_at": _iso(row.resolved_at),
        "escalation_level": row.escalation_level,
        "linked_vendor_id": row.linked_vendor_id,
        "linked_vendor_name": row.linked_vendor_name,
        "linked_region": row.linked_region,
        "priority": row.priority,
        "recommended_action": row.recommended_action,
        "linked_evidence_ids": row.linked_evidence_ids or [],
        "audit_preview": row.audit_preview,
        "workstream": row.workstream,
        # A legacy row has no due date; derive it from its start + policy so
        # overdue/at-risk works for pre-existing tickets too.
        "due_at": _iso(row.due_at) or ticketing.due_at(row.created_at, policy),
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _audit_dict(row: AuditEvent) -> dict[str, Any]:
    return {
        "id": row.id,
        "case_id": row.case_id,
        "ticket_id": row.ticket_id,
        "event_type": row.event_type,
        "actor": row.actor,
        "role": row.role,
        "description": row.description,
        "timestamp": _iso(row.timestamp),
    }


def _vendor_dict(row: Vendor) -> dict[str, Any]:
    return {
        "id": row.id,
        "name": row.name,
        "region": row.region,
        "district": row.district,
        "assigned_schools": row.assigned_schools or [],
        "daily_meal_volume": row.daily_meal_volume,
        "compliance_status": row.compliance_status,
        "risk_score": row.risk_score,
        "risk_trend": row.risk_trend or [],
        "watchlist_status": row.watchlist_status,
        "watchlist_reason": row.watchlist_reason,
        "last_inspection_date": row.last_inspection_date,
        "repeated_issue_categories": row.repeated_issue_categories or [],
        "coverage_notes": row.coverage_notes,
        "recommended_action": row.recommended_action,
    }


# ── Domain dict -> column values ─────────────────────────────────────────
# Inverse of the readers above, minus derived/foreign keys set by the caller.

_CASE_COLUMNS = ("vendor_id", "school", "region", "district", "vendor_name_override",
                 "vendor_source_note", "issue_category", "priority_label", "severity",
                 "status", "title", "assigned_investigator", "assigned_unit", "case_type",
                 "case_subtype", "impact_summary", "primary_owner", "handling_team",
                 "secondary_owner", "watchers", "handling_strategy", "related_case_id",
                 "case_relationship", "blockers", "resolution_summary")

_SIGNAL_COLUMNS = ("case_id", "source", "source_confidence", "urgency", "status", "summary",
                   "text", "vendor_id", "vendor_name", "region", "district", "school",
                   "issue_category", "attachment_path", "attachment_title",
                   "attachment_source", "attachment_note", "reviewer_note")

_EVIDENCE_COLUMNS = ("case_id", "signal_id", "type", "title", "file_path", "linked_entity",
                     "source", "ocr_result", "image_text_match_score", "duplicate_score",
                     "confidence_score", "review_status", "reviewer_note",
                     "unlinked_from_case")

_RISK_COLUMNS = ("case_id", "vendor_id", "vendor_name", "region", "severity_score",
                 "confidence_score", "nutrition_concern_score", "cost_anomaly_score",
                 "anomaly_score", "final_priority_score", "priority_label", "explanation",
                 "recommended_action")

_TICKET_COLUMNS = ("case_id", "title", "description", "status", "severity", "impact",
                   "urgency", "sla_policy", "sla", "assignee", "assignment_group",
                   "assigned_unit", "category", "labels", "notes", "escalation_level",
                   "linked_vendor_id", "linked_vendor_name", "linked_region", "priority",
                   "recommended_action", "linked_evidence_ids", "audit_preview", "workstream")

_AUDIT_COLUMNS = ("case_id", "ticket_id", "event_type", "actor", "role", "description")

# table spec: (model, primary key attr, dict key for the pk, writable columns,
# datetime columns)
_SPECS = {
    "case": (Case, "case_id", "case_id", _CASE_COLUMNS, ("created_at", "updated_at", "due_at")),
    "signal": (Signal, "id", "id", _SIGNAL_COLUMNS, ("created_at",)),
    "evidence": (Evidence, "id", "id", _EVIDENCE_COLUMNS, ("created_at",)),
    "risk": (RiskAssessment, "id", "id", _RISK_COLUMNS, ("computed_at",)),
    "ticket": (Ticket, "id", "id", _TICKET_COLUMNS, ("created_at", "updated_at", "due_at", "resolved_at")),
    "audit": (AuditEvent, "id", "id", _AUDIT_COLUMNS, ("timestamp",)),
}


def persist(kind: str, item: dict[str, Any], *, seeded: bool = False,
            seed_group: str | None = None) -> None:
    """Upsert one domain dict into its table.

    Called after the in-memory mutation, so the dict is already in its final
    state.  Never raises: a persistence failure must not roll back an operator
    action that the UI has already been told succeeded.
    """
    if not _enabled:
        return
    model, pk_attr, pk_key, columns, dt_columns = _SPECS[kind]
    pk_value = item.get(pk_key)
    try:
        with SessionLocal() as session:
            row = session.get(model, pk_value)
            if row is None:
                row = model(**{pk_attr: pk_value})
                row.is_seeded = seeded
                row.seed_group = seed_group
                session.add(row)
            for name in columns:
                if name in item:
                    setattr(row, name, item[name])
            for name in dt_columns:
                if name in item:
                    setattr(row, name, _dt(item[name]))
            session.commit()
    except Exception as exc:  # pragma: no cover - depends on DB availability
        log.warning("persist(%s, %s) failed: %s", kind, pk_value, exc)


def delete_row(kind: str, pk_value: Any) -> None:
    """Remove one row (used when a runtime object is discarded)."""
    if not _enabled:
        return
    model, pk_attr, _, _, _ = _SPECS[kind]
    try:
        with SessionLocal() as session:
            session.execute(delete(model).where(getattr(model, pk_attr) == pk_value))
            session.commit()
    except Exception as exc:  # pragma: no cover
        log.warning("delete_row(%s, %s) failed: %s", kind, pk_value, exc)


# ── Startup hydration ────────────────────────────────────────────────────
def _replace(target: list, rows: list[dict[str, Any]]) -> None:
    """Swap list contents in place.

    ``demo_data`` aliases these lists at import time (``VENDORS = sd.VENDORS``),
    so rebinding the module attribute would leave the API reading the stale
    object.  Mutating in place keeps every alias pointing at live data.
    """
    target[:] = rows


def hydrate() -> bool:
    """Load DB state into the seed_data collections.  Returns True on success.

    An empty ``cases`` table means the DB has never been seeded; the in-memory
    literals are left alone and persistence stays off so the app still boots
    into a working demo.  Run ``python -m app.dbctl seed`` to populate it.
    """
    global _enabled
    try:
        with SessionLocal() as session:
            cases = session.execute(select(Case)).scalars().all()
            if not cases:
                log.warning("DB reachable but empty — run `python -m app.dbctl seed`. "
                            "Falling back to in-memory demo data.")
                return False

            vendors = session.execute(select(Vendor)).scalars().all()
            signals = session.execute(select(Signal).order_by(Signal.id)).scalars().all()
            evidence = session.execute(select(Evidence).order_by(Evidence.id)).scalars().all()
            risks = session.execute(select(RiskAssessment).order_by(RiskAssessment.id)).scalars().all()
            tickets = session.execute(select(Ticket).order_by(Ticket.id)).scalars().all()
            audit = session.execute(
                select(AuditEvent).order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
            ).scalars().all()

        # `vnd-unknown` is a FK target for cases with no identified vendor, but
        # it must stay out of VENDORS so watchlist and heatmap metrics are not
        # skewed by a placeholder.  It is resolvable through VENDOR_BY_ID only.
        _replace(sd.VENDORS, [_vendor_dict(r) for r in vendors
                              if r.id != sd.UNIDENTIFIED_VENDOR["id"]])
        _replace(sd.CASES, [_case_dict(r) for r in cases])
        _replace(sd.SIGNALS, [_signal_dict(r) for r in signals])
        _replace(sd.EVIDENCE, [_evidence_dict(r) for r in evidence])
        _replace(sd.RISK, [_risk_dict(r) for r in risks])
        _replace(sd.TICKETS, [_ticket_dict(r) for r in tickets])
        _replace(sd.AUDIT, [_audit_dict(r) for r in audit])

        # Index dicts are rebuilt in place for the same aliasing reason.
        sd.VENDOR_BY_ID.clear()
        sd.VENDOR_BY_ID.update({v["id"]: v for v in sd.VENDORS})
        sd.VENDOR_BY_ID[sd.UNIDENTIFIED_VENDOR["id"]] = sd.UNIDENTIFIED_VENDOR
        sd.CASE_BY_ID.clear()
        sd.CASE_BY_ID.update({c["case_id"]: c for c in sd.CASES})
        sd.RISK_BY_CASE.clear()
        sd.RISK_BY_CASE.update({r["case_id"]: r for r in sd.RISK})
        sd.TICKET_BY_CASE.clear()
        sd.TICKET_BY_CASE.update({t["case_id"]: t for t in sd.TICKETS})

        _enabled = True
        log.info("Hydrated from DB: %d cases, %d signals, %d evidence, %d tickets.",
                 len(sd.CASES), len(sd.SIGNALS), len(sd.EVIDENCE), len(sd.TICKETS))
        return True
    except Exception as exc:
        log.warning("DB hydration failed (%s). Falling back to in-memory demo data.", exc)
        return False
