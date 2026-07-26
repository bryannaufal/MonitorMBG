"""Developer CLI for the MonitorMBG database.

    python -m app.dbctl seed              # baseline demo data (MBG-001..010)
    python -m app.dbctl seed --scenario belatung
    python -m app.dbctl reset             # wipe runtime rows, reload baseline
    python -m app.dbctl reset --empty     # wipe everything, seed nothing
    python -m app.dbctl status            # row counts and seed groups

Seeded rows carry ``is_seeded=True`` and a ``seed_group``; rows an operator
created at runtime carry ``is_seeded=False``.  ``status`` reports that split so
you can see at a glance what is demo data and what an operator produced.

``reset`` is all-or-nothing by design: runtime rows reference seed rows (fusion
evidence points at a seeded signal), so one layer cannot be dropped out from
under the other.  Scenario selection happens at seed time, not delete time.

Run ``alembic upgrade head`` before the first seed.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import delete, func, select

from app import seed_data as sd
from app.models.oversight import (
    AuditEvent,
    Case,
    Evidence,
    RiskAssessment,
    Signal,
    Ticket,
    Vendor,
    VerificationReview,
)
from app.persistence import SessionLocal, _dt

BASELINE = "baseline"
# Signals staged for the evidence-fusion demo; they intentionally start
# unlinked so an operator can run the review flow end to end.
SCENARIOS = {"belatung": (19, 20)}

# Child-to-parent order, safe for foreign keys.
_DELETE_ORDER = (AuditEvent, VerificationReview, Ticket, RiskAssessment, Evidence, Signal, Case, Vendor)


def _wipe(session) -> None:
    """Delete every oversight row, children first.

    Deliberately unfiltered: runtime rows reference seed rows (evidence created
    during fusion points at a seeded signal), so seeds cannot be dropped while
    runtime work still refers to them.  Reset is therefore all-or-nothing —
    ``is_seeded``/``seed_group`` exist to *report* provenance and to let a
    scenario be seeded selectively, not to delete one layer out from under
    the other.
    """
    for model in _DELETE_ORDER:
        session.execute(delete(model))


def _load_baseline(session, scenarios: set[str]) -> None:
    """Insert the canonical demo dataset.

    ``seed_data`` is the single source shared with the API and the frontend
    fallback, so seeding cannot drift from what the demo renders.
    """
    scenario_ids = {sid for name in scenarios for sid in SCENARIOS[name]}
    skipped = {sid for name, ids in SCENARIOS.items() if name not in scenarios for sid in ids}

    def group_for(signal_id: int) -> str:
        for name, ids in SCENARIOS.items():
            if signal_id in ids:
                return name
        return BASELINE

    # `vnd-unknown` is a FK target for cases with no identified vendor; it is
    # kept out of VENDORS so it never skews watchlist/heatmap metrics.
    for v in [*sd.VENDORS, sd.UNIDENTIFIED_VENDOR]:
        session.add(Vendor(**v, is_seeded=True, seed_group=BASELINE))
    session.flush()

    for c in sd.CASES:
        session.add(Case(
            case_id=c["case_id"], vendor_id=c["vendor_id"], school=c["school"],
            region=c.get("region"), district=c.get("district"),
            issue_category=c["issue_category"], priority_label=c["priority_label"],
            severity=c.get("severity") or c["priority_label"],
            status=c["status"], title=c["title"],
            created_at=_dt(c["created_at"]), updated_at=_dt(c["updated_at"]),
            is_seeded=True, seed_group=BASELINE,
        ))
    session.flush()

    for s in sd.SIGNALS:
        if s["id"] in skipped:
            continue
        session.add(Signal(
            id=s["id"], case_id=s.get("case_id"), source=s["source"],
            source_confidence=s["source_confidence"], urgency=s["urgency"], status=s["status"],
            summary=s["summary"], text=s["text"], vendor_id=s.get("vendor_id"),
            vendor_name=s.get("vendor_name", ""), region=s.get("region", ""),
            district=s.get("district", ""), school=s.get("school", ""),
            issue_category=s.get("issue_category", ""),
            attachment_path=s.get("attachment_path"), attachment_title=s.get("attachment_title"),
            attachment_source=s.get("attachment_source"), attachment_note=s.get("attachment_note"),
            reviewer_note=s.get("reviewer_note"),
            created_at=_dt(s["created_at"]),
            is_seeded=True, seed_group=group_for(s["id"]),
        ))
    session.flush()

    for e in sd.EVIDENCE:
        session.add(Evidence(
            id=e["id"], case_id=e["case_id"], signal_id=e.get("signal_id"), type=e["type"],
            title=e["title"], file_path=e["file_path"], linked_entity=e["linked_entity"],
            source=e["source"], ocr_result=e.get("ocr_result"),
            image_text_match_score=e.get("image_text_match_score"),
            duplicate_score=e.get("duplicate_score"), confidence_score=e["confidence_score"],
            review_status=e["review_status"], reviewer_note=e["reviewer_note"],
            unlinked_from_case=bool(e.get("unlinked_from_case")),
            created_at=_dt(e["created_at"]), is_seeded=True, seed_group=BASELINE,
        ))
        session.add(VerificationReview(
            evidence_id=e["id"], case_id=e["case_id"], reviewer="Operator Dewi",
            result=e["review_status"], note="Tinjauan awal pra-verifikasi; keputusan akhir oleh operator.",
            reviewed_at=_dt(e["created_at"]),
        ))
    session.flush()

    for r in sd.RISK:
        session.add(RiskAssessment(
            id=r["id"], case_id=r["case_id"], vendor_id=r["vendor_id"], vendor_name=r["vendor_name"],
            region=r["region"], severity_score=r["severity_score"], confidence_score=r["confidence_score"],
            nutrition_concern_score=r["nutrition_concern_score"], cost_anomaly_score=r["cost_anomaly_score"],
            anomaly_score=r["anomaly_score"], final_priority_score=r["final_priority_score"],
            priority_label=r["priority_label"], explanation=r["explanation"],
            recommended_action=r["recommended_action"], computed_at=_dt(r["computed_at"]),
            is_seeded=True, seed_group=BASELINE,
        ))

    for t in sd.TICKETS:
        session.add(Ticket(
            id=t["id"], case_id=t["case_id"], title=t["title"], description=t.get("description"),
            status=t["status"], severity=t.get("severity"), impact=t.get("impact"),
            urgency=t.get("urgency"), sla_policy=t.get("sla_policy"), sla=t["sla"],
            assignee=t.get("assignee"), assignment_group=t.get("assignment_group"),
            assigned_unit=t["assigned_unit"], category=t.get("category"),
            labels=t.get("labels") or [], notes=t.get("notes") or [],
            escalation_level=t["escalation_level"],
            linked_vendor_id=t["linked_vendor_id"], linked_vendor_name=t["linked_vendor_name"],
            linked_region=t["linked_region"], priority=t["priority"],
            recommended_action=t["recommended_action"], linked_evidence_ids=t["linked_evidence_ids"],
            audit_preview=t["audit_preview"], workstream=t.get("workstream"),
            due_at=_dt(t.get("due_at")), resolved_at=_dt(t.get("resolved_at")),
            created_at=_dt(t["created_at"]),
            updated_at=_dt(t["updated_at"]), is_seeded=True, seed_group=BASELINE,
        ))

    for a in sd.AUDIT:
        session.add(AuditEvent(
            id=a["id"], case_id=a["case_id"], ticket_id=a.get("ticket_id"), event_type=a["event_type"],
            actor=a["actor"], role=a["role"], description=a["description"],
            timestamp=_dt(a["timestamp"]), is_seeded=True, seed_group=BASELINE,
        ))

    if scenario_ids:
        print(f"  + skenario: {', '.join(sorted(scenarios))} (sinyal {sorted(scenario_ids)})")


def cmd_seed(args) -> None:
    scenarios = set(args.scenario or [])
    unknown = scenarios - SCENARIOS.keys()
    if unknown:
        sys.exit(f"Skenario tidak dikenal: {', '.join(sorted(unknown))}. "
                 f"Pilihan: {', '.join(sorted(SCENARIOS))}")
    with SessionLocal() as session:
        _wipe(session)
        _load_baseline(session, scenarios)
        session.commit()
    print(f"✓ Seed selesai: {len(sd.VENDORS)} vendor, {len(sd.CASES)} kasus, "
          f"{len(sd.EVIDENCE)} bukti, {len(sd.TICKETS)} tiket.")


def cmd_reset(args) -> None:
    with SessionLocal() as session:
        if args.empty:
            _wipe(session)
            session.commit()
            print("✓ Database dikosongkan. Tidak ada seed dimuat.")
            return
        _wipe(session)
        _load_baseline(session, set(args.scenario or []))
        session.commit()
    print("✓ Reset ke baseline selesai.")


def cmd_status(_args) -> None:
    with SessionLocal() as session:
        print(f"{'tabel':<20}{'total':>8}{'seed':>8}{'runtime':>9}")
        for model in reversed(_DELETE_ORDER):
            total = session.scalar(select(func.count()).select_from(model))
            if not hasattr(model, "is_seeded"):
                print(f"{model.__tablename__:<20}{total:>8}{'-':>8}{'-':>9}")
                continue
            seeded = session.scalar(
                select(func.count()).select_from(model).where(model.is_seeded.is_(True)))
            print(f"{model.__tablename__:<20}{total:>8}{seeded:>8}{total - seeded:>9}")
        groups = session.execute(
            select(Signal.seed_group, func.count()).group_by(Signal.seed_group)).all()
        print("\nseed_group (signals):", ", ".join(f"{g or 'runtime'}={n}" for g, n in groups) or "-")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.dbctl", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed", help="wipe and load baseline demo data")
    p_seed.add_argument("--scenario", action="append", choices=sorted(SCENARIOS),
                        help="also load a scenario seed (repeatable)")
    p_seed.set_defaults(func=cmd_seed)

    p_reset = sub.add_parser("reset", help="restore baseline, or empty the database")
    p_reset.add_argument("--empty", action="store_true", help="delete everything, seed nothing")
    p_reset.add_argument("--scenario", action="append", choices=sorted(SCENARIOS))
    p_reset.set_defaults(func=cmd_reset)

    sub.add_parser("status", help="show row counts per table").set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
