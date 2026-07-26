"""Round-trip check: a runtime mutation must survive a re-hydrate.

Requires a migrated, seeded Postgres (``python -m app.dbctl seed``); skipped
otherwise so the suite still runs on a machine without docker.

This is the regression guard for the bug the persistence layer exists to fix:
a case fused from signals used to vanish on restart.  Each test undoes its own
writes so the developer database is left as it was found.
"""

from __future__ import annotations

import pytest

from app import demo_data, persistence, seed_data as sd

# Other suites assert that these specific signals are still unlinked, so the
# probe below never consumes one of them.
_RESERVED_SIGNAL_IDS = {17, 19, 20}


def _reload() -> None:
    """Simulate a backend restart: drop in-memory state, reload from DB."""
    sd.CASES.clear()
    sd.CASE_BY_ID.clear()
    sd.TICKETS.clear()
    assert persistence.hydrate(), "re-hydrate after a wipe must succeed"
    demo_data.rebuild_derived()


def _discard_case(case_id: str, signal_id: int) -> None:
    """Undo the probe so repeated runs start from the same database state."""
    from sqlalchemy import delete, update

    from app.models.oversight import AuditEvent, Case, Evidence, RiskAssessment, Signal

    with persistence.SessionLocal() as session:
        session.execute(delete(Evidence).where(Evidence.case_id == case_id))
        session.execute(delete(AuditEvent).where(AuditEvent.case_id == case_id))
        session.execute(delete(RiskAssessment).where(RiskAssessment.case_id == case_id))
        session.execute(update(Signal).where(Signal.case_id == case_id)
                        .values(case_id=None, status="Belum Dibentuk Kasus"))
        session.execute(delete(Case).where(Case.case_id == case_id))
        session.commit()
    _reload()


def _drop_orphan_audit() -> None:
    """Remove audit rows the probe produced before its case existed.

    ``review_signal`` logs ``signal_reviewed`` with ``case_id=None``, so those
    rows are not covered by the per-case cleanup above.
    """
    from sqlalchemy import delete

    from app.models.oversight import AuditEvent

    with persistence.SessionLocal() as session:
        session.execute(delete(AuditEvent).where(
            AuditEvent.is_seeded.is_(False), AuditEvent.case_id.is_(None)))
        session.commit()
    _reload()


def test_runtime_case_survives_restart(persistent_db):
    """A case created from a signal is still there after re-hydration."""
    from app import review_store

    signal = next((s for s in reversed(sd.SIGNALS)
                   if not s.get("case_id") and s["id"] not in _RESERVED_SIGNAL_IDS), None)
    if signal is None:
        pytest.skip("no spare unlinked signal available to review")
    signal_id = signal["id"]

    result = review_store.review_signal(signal_id, {
        "decision": "create",
        "new_case": {"title": "Persistence round-trip probe"},
        "override": {"operator_adjusted": False, "priority_label": "Sedang",
                     "final_priority_score": 50},
    })
    case_id = result["case_id"]

    _reload()
    try:
        assert case_id in sd.CASE_BY_ID, f"{case_id} did not survive the reload"
        detail = demo_data.case_detail(case_id)
        assert detail["title"] == "Persistence round-trip probe"
        # The reviewed signal must still be attached, not orphaned.
        assert signal_id in [s["id"] for s in detail["signals"]]
    finally:
        _discard_case(case_id, signal_id)
        _drop_orphan_audit()


def test_ticket_status_survives_restart(persistent_db):
    """A ticket status change is written through, not held in memory."""
    if not sd.TICKETS:
        pytest.skip("no seeded tickets")
    ticket = sd.TICKETS[0]
    ticket_id, original = ticket["id"], ticket["status"]
    new_status = "Eskalasi" if original != "Eskalasi" else "Selesai"

    ticket["status"] = new_status
    persistence.persist("ticket", ticket)

    _reload()
    try:
        reloaded = next(t for t in sd.TICKETS if t["id"] == ticket_id)
        assert reloaded["status"] == new_status
    finally:
        restored = next(t for t in sd.TICKETS if t["id"] == ticket_id)
        restored["status"] = original
        persistence.persist("ticket", restored)
