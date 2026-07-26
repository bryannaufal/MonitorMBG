"""Ticketing domain tests: SLA, inheritance, assignment, lifecycle, monitoring.

The regression these exist to prevent: a `Kritis` case producing a child ticket
with a 72h SLA because the create endpoint carried a literal default and never
read the parent.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone

import pytest

from app import demo_data as demo_data_module
from app import review_store as review_store_module
from app import seed_data as seed_data_module
from app import ticketing
from tests.test_create_fusion import create_payload, make_client

_RUNTIME_MODULES = (seed_data_module, demo_data_module, review_store_module)


@pytest.fixture(autouse=True)
def reset_runtime_state():
    """Each test starts from clean seed state; signal #19 is reusable."""
    for module in _RUNTIME_MODULES:
        importlib.reload(module)
    yield
    for module in _RUNTIME_MODULES:
        importlib.reload(module)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ticket(**overrides) -> dict:
    """Minimal ticket dict; overrides supply whatever the test cares about."""
    created = _now() - timedelta(hours=1)
    base = {
        "id": "tkt-x", "case_id": "case-001", "status": "Sedang Ditinjau",
        "severity": "Sedang", "sla_policy": "P3", "sla": "48h",
        "assignee": "Operator A", "assignment_group": "Unit X",
        "created_at": created.isoformat(),
        "updated_at": created.isoformat(),
        "due_at": ticketing.due_at(created, "P3"),
        "resolved_at": None,
    }
    return {**base, **overrides}


# ── SLA determination ────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "severity,expected",
    [("Kritis", "P1"), ("Critical", "P1"), ("Tinggi", "P2"), ("High", "P2"),
     ("Sedang", "P3"), ("Rendah", "P4"), ("Low", "P4")],
)
def test_policy_follows_severity(severity, expected):
    assert ticketing.policy_for(severity) == expected


def test_critical_never_falls_back_to_72h():
    """The headline bug: `Kritis` must not resolve to the 72h band."""
    for impact in ticketing.IMPACT_LEVELS:
        for urgency in ticketing.URGENCY_LEVELS:
            policy = ticketing.policy_for("Kritis", impact, urgency)
            assert policy == "P1"
            assert ticketing.sla_label(policy) != "72h"


def test_unknown_severity_uses_the_stated_middle_default():
    # Explicit, documented default rather than a silent 72h.
    assert ticketing.policy_for(None) == "P3"
    assert ticketing.policy_for("nonsense") == "P3"


def test_impact_and_urgency_shift_the_band():
    assert ticketing.policy_for("Sedang", "Luas", "Normal") == "P2"
    assert ticketing.policy_for("Sedang", None, "Segera") == "P2"
    assert ticketing.policy_for("Sedang", "Terbatas", "Terjadwal") == "P4"
    # Only 72h when severity genuinely is low.
    assert ticketing.sla_label(ticketing.policy_for("Rendah")) == "72h"


def test_legacy_sla_label_parses_back_to_hours():
    assert ticketing.hours_from_label("72h") == 72
    assert ticketing.hours_from_label("4h") == 4
    assert ticketing.hours_from_label(None) is None
    assert ticketing.hours_from_label("segera") is None


def test_due_at_matches_the_policy_window():
    start = _now()
    for code, spec in ticketing.SLA_POLICIES.items():
        deadline = datetime.fromisoformat(ticketing.due_at(start, code))
        assert deadline - start == timedelta(hours=spec["hours"])


# ── Parent -> child inheritance ──────────────────────────────────────────
def test_child_inherits_parent_severity_by_default():
    case = {"severity": "Kritis", "priority_label": "Kritis"}
    assert ticketing.resolve_severity(case, None) == ("Kritis", "inherited_from_case")


def test_child_may_override_parent_severity():
    case = {"severity": "Kritis"}
    assert ticketing.resolve_severity(case, "Rendah") == ("Rendah", "override")


def test_inheritance_falls_back_to_priority_label():
    assert ticketing.resolve_severity({"priority_label": "Tinggi"}, None)[0] == "Tinggi"


def test_severity_default_is_named_when_parent_has_none():
    severity, rule = ticketing.resolve_severity({}, None)
    assert (severity, rule) == ("Sedang", "default_no_parent_severity")


# ── Assignment ───────────────────────────────────────────────────────────
def test_assignment_inherits_case_owner_and_team():
    case = {"primary_owner": "Rina", "handling_team": "Unit A"}
    assert ticketing.resolve_assignment(case, None, None) == ("Rina", "Unit A", "inherited_from_case")


def test_explicit_assignment_wins_over_inheritance():
    case = {"primary_owner": "Rina", "handling_team": "Unit A"}
    assert ticketing.resolve_assignment(case, "Budi", "Unit B") == ("Budi", "Unit B", "explicit")


def test_group_only_assignment_leaves_individual_pending():
    assignee, group, rule = ticketing.resolve_assignment({}, None, "Unit C")
    assert (assignee, group) == (None, "Unit C")
    assert rule == "group_explicit_pending_individual"


def test_unowned_case_yields_an_explicitly_unassigned_ticket():
    assignee, group, rule = ticketing.resolve_assignment({}, None, None)
    assert assignee is None
    assert group == ticketing.UNASSIGNED
    assert rule == "unassigned_needs_triage"


# ── Status lifecycle ─────────────────────────────────────────────────────
def test_new_ticket_cannot_jump_straight_to_resolved():
    assert not ticketing.can_transition("Baru", "Selesai")
    assert ticketing.can_transition("Baru", "Sedang Ditinjau")
    assert ticketing.can_transition("Sedang Ditinjau", "Selesai")


def test_cancelled_is_terminal():
    assert ticketing.TRANSITIONS["Dibatalkan"] == set()


def test_closed_reopens_only_into_review():
    assert ticketing.can_transition("Ditutup", "Sedang Ditinjau")
    assert not ticketing.can_transition("Ditutup", "Selesai")


def test_every_transition_target_is_a_known_status():
    for source, targets in ticketing.TRANSITIONS.items():
        assert source in ticketing.TICKET_STATUSES
        assert targets <= ticketing.TICKET_STATUSES


# ── Overdue / at-risk detection ──────────────────────────────────────────
def test_fresh_ticket_is_on_track():
    state = ticketing.sla_state(_ticket())
    assert state["sla_state"] == "on_track"
    assert not state["at_risk"] and not state["overdue"]


def test_ticket_past_75_percent_of_window_is_at_risk():
    created = _now() - timedelta(hours=40)  # 40 of 48h elapsed
    state = ticketing.sla_state(_ticket(
        created_at=created.isoformat(), due_at=ticketing.due_at(created, "P3")))
    assert state["sla_state"] == "at_risk"
    assert state["at_risk"] and not state["overdue"]


def test_ticket_past_deadline_is_overdue_and_breached():
    created = _now() - timedelta(hours=60)
    state = ticketing.sla_state(_ticket(
        created_at=created.isoformat(), due_at=ticketing.due_at(created, "P3")))
    assert state["sla_state"] == "overdue"
    assert state["overdue"] and state["breached"]
    assert state["hours_remaining"] < 0


def test_waiting_on_vendor_pauses_the_clock():
    """An external wait is not the operator's breach."""
    created = _now() - timedelta(hours=60)
    state = ticketing.sla_state(_ticket(
        status="Menunggu Klarifikasi Vendor",
        created_at=created.isoformat(), due_at=ticketing.due_at(created, "P3")))
    assert state["sla_state"] == "paused"
    assert not state["overdue"] and not state["breached"]


def test_completion_is_judged_against_resolution_time():
    created = _now() - timedelta(hours=60)
    on_time = (created + timedelta(hours=10)).isoformat()
    met = ticketing.sla_state(_ticket(
        status="Selesai", created_at=created.isoformat(),
        due_at=ticketing.due_at(created, "P3"), resolved_at=on_time))
    assert met["sla_state"] == "met" and not met["breached"]

    late = ticketing.sla_state(_ticket(
        status="Selesai", created_at=created.isoformat(),
        due_at=ticketing.due_at(created, "P3"),
        resolved_at=(created + timedelta(hours=55)).isoformat()))
    assert late["sla_state"] == "breached" and late["breached"]


def test_ticket_without_a_due_date_reports_unknown_not_on_track():
    assert ticketing.sla_state(_ticket(due_at=None))["sla_state"] == "unknown"


# ── Monitoring counters ──────────────────────────────────────────────────
def test_summary_counts_each_facet():
    created = _now() - timedelta(hours=60)
    tickets = [
        _ticket(id="a", status="Baru"),
        _ticket(id="b", status="Sedang Ditinjau"),
        _ticket(id="c", status="Menunggu Klarifikasi Vendor"),
        _ticket(id="d", status="Selesai", resolved_at=_now().isoformat()),
        _ticket(id="e", status="Verifikasi Lapangan", assignee=None,
                created_at=created.isoformat(), due_at=ticketing.due_at(created, "P3")),
    ]
    s = ticketing.summarise(tickets)
    assert s["total"] == 5
    assert s["open"] == 1 and s["in_progress"] == 2 and s["waiting"] == 1
    assert s["resolved"] == 1 and s["completed"] == 1
    assert s["overdue"] == 1 and s["paused"] == 1
    assert s["unassigned"] == 1
    assert s["met_sla"] == 1


def test_summary_of_no_tickets_is_all_zero():
    assert set(ticketing.summarise([]).values()) == {0}


# ── API: create / update / monitoring end to end ─────────────────────────
@pytest.mark.asyncio
async def test_critical_case_produces_a_critical_child_ticket():
    """End-to-end regression for the reported bug."""
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        await client.patch(f"/api/v1/cases/{cid}", json={"severity": "Kritis"})

        created = (await client.post(f"/api/v1/cases/{cid}/tickets",
                                     json={"title": "Respons darurat"})).json()
        ticket = created["ticket"]
        assert ticket["severity"] == "Kritis"
        assert ticket["sla"] == "4h" and ticket["sla_policy"] == "P1"
        assert ticket["sla"] != "72h"
        assert created["applied_rules"]["severity"] == "inherited_from_case"
        assert ticket["due_at"] and ticket["sla_state"] == "on_track"


@pytest.mark.asyncio
async def test_create_accepts_the_full_operational_field_set():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        ticket = (await client.post(f"/api/v1/cases/{cid}/tickets", json={
            "title": "Inspeksi dapur", "description": "Cek higiene",
            "severity": "Tinggi", "impact": "Luas", "urgency": "Segera",
            "assignee": "Budi", "assignment_group": "Unit Higiene",
            "category": "higiene", "labels": ["lapangan"], "notes": "Mulai besok",
            "workstream": "Lapangan",
        })).json()["ticket"]
        assert ticket["description"] == "Cek higiene"
        assert ticket["assignee"] == "Budi" and ticket["assignment_group"] == "Unit Higiene"
        assert ticket["labels"] == ["lapangan"] and ticket["notes"][0]["note"] == "Mulai besok"
        assert ticket["category"] == "higiene"
        # Tinggi + Luas impact + Segera urgency escalates one band to P1.
        assert ticket["sla_policy"] == "P1"


@pytest.mark.asyncio
async def test_explicit_sla_policy_overrides_severity_derivation():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        body = (await client.post(f"/api/v1/cases/{cid}/tickets",
                                  json={"title": "Pantauan rutin", "severity": "Kritis",
                                        "sla_policy": "P4"})).json()
        assert body["ticket"]["sla"] == "72h"
        # An explicit 72h on a Kritis ticket is allowed, but it is recorded as a
        # deliberate operator choice rather than a silent fallback.
        assert body["applied_rules"]["sla"] == "explicit_policy"


@pytest.mark.asyncio
async def test_unknown_sla_policy_is_rejected():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        res = await client.post(f"/api/v1/cases/{cid}/tickets",
                                json={"title": "X", "sla_policy": "P9"})
        assert res.status_code == 422


@pytest.mark.asyncio
async def test_raising_severity_recalculates_sla_and_due_date():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        ticket = (await client.post(f"/api/v1/cases/{cid}/tickets",
                                    json={"title": "Tindak lanjut", "severity": "Rendah"})).json()["ticket"]
        assert ticket["sla"] == "72h"

        body = (await client.patch(f"/api/v1/tickets/{ticket['id']}",
                                   json={"severity": "Kritis"})).json()
        assert body["ticket"]["sla"] == "4h" and body["ticket"]["sla_policy"] == "P1"
        assert any(e["event_type"] == "ticket_sla_changed" for e in body["audit_events"])


@pytest.mark.asyncio
async def test_reassignment_is_recorded_with_both_endpoints():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        ticket = (await client.post(f"/api/v1/cases/{cid}/tickets",
                                    json={"title": "T", "assignee": "Rina"})).json()["ticket"]
        body = (await client.patch(f"/api/v1/tickets/{ticket['id']}",
                                   json={"assignee": "Budi", "reassign_reason": "Rina cuti"})).json()
        assert body["ticket"]["assignee"] == "Budi"
        event = next(e for e in body["audit_events"] if e["event_type"] == "ticket_reassigned")
        assert "Rina" in event["description"] and "Budi" in event["description"]
        assert "Rina cuti" in event["description"]


@pytest.mark.asyncio
async def test_invalid_status_transition_is_rejected_with_a_reason():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        ticket = (await client.post(f"/api/v1/cases/{cid}/tickets", json={"title": "T"})).json()["ticket"]
        res = await client.patch(f"/api/v1/tickets/{ticket['id']}/status", json={"status": "Selesai"})
        assert res.status_code == 422 and "tidak diizinkan" in res.json()["detail"]
        assert (await client.patch(f"/api/v1/tickets/{ticket['id']}/status",
                                   json={"status": "Mengambang"})).status_code == 422


@pytest.mark.asyncio
async def test_resolving_stamps_resolved_at_and_reopening_clears_it():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        ticket = (await client.post(f"/api/v1/cases/{cid}/tickets", json={"title": "T"})).json()["ticket"]
        tid = ticket["id"]
        await client.patch(f"/api/v1/tickets/{tid}/status", json={"status": "Sedang Ditinjau"})
        done = (await client.patch(f"/api/v1/tickets/{tid}/status", json={"status": "Selesai"})).json()["ticket"]
        assert done["resolved_at"] and done["sla_state"] == "met"

        reopened = (await client.patch(f"/api/v1/tickets/{tid}/status",
                                       json={"status": "Sedang Ditinjau"})).json()["ticket"]
        assert reopened["resolved_at"] is None


@pytest.mark.asyncio
async def test_ticket_list_exposes_summary_and_sla_state():
    async with await make_client() as client:
        body = (await client.get("/api/v1/tickets")).json()
        assert body["summary"]["total"] == body["total"]
        assert all("sla_state" in t for t in body["items"])
        assert set(body["sla_policies"]) == {"P1", "P2", "P3", "P4"}


@pytest.mark.asyncio
async def test_case_and_ticket_board_report_the_same_counters():
    """Monitoring must have one source of truth, not two tallies."""
    async with await make_client() as client:
        detail = (await client.get("/api/v1/cases/case-001")).json()
        board = (await client.get("/api/v1/tickets?case_id=case-001")).json()
        assert detail["ticket_summary"]["total"] == board["total"]


@pytest.mark.asyncio
async def test_ticket_audit_log_is_retrievable():
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        ticket = (await client.post(f"/api/v1/cases/{cid}/tickets", json={"title": "T"})).json()["ticket"]
        await client.patch(f"/api/v1/tickets/{ticket['id']}", json={"note": "Progres awal"})
        events = (await client.get(f"/api/v1/tickets/{ticket['id']}/audit")).json()["items"]
        assert any(e["event_type"] == "ticket_progress_note" for e in events)
        assert all(e["ticket_id"] == ticket["id"] for e in events)


@pytest.mark.asyncio
async def test_case_without_tickets_reports_no_ticket_sla():
    """A case with no child ticket must not display an invented 72h target."""
    async with await make_client() as client:
        cid = (await client.post("/api/v1/signals/19/review", json=create_payload())).json()["case_id"]
        detail = (await client.get(f"/api/v1/cases/{cid}")).json()
        assert detail["tickets"] == [] and detail["sla_status"] == "Tanpa SLA tiket"
        assert "72h" not in detail["sla_status"]


# ── Backward compatibility ───────────────────────────────────────────────
def test_seed_tickets_carry_a_policy_and_due_date():
    from app import seed_data as sd

    for ticket in sd.TICKETS:
        assert ticket["sla_policy"] in ticketing.SLA_POLICIES
        assert ticket["due_at"]
        assert ticket["status"] in ticketing.TICKET_STATUSES


def test_no_seed_ticket_pairs_critical_severity_with_72h():
    from app import seed_data as sd

    assert not [t for t in sd.TICKETS
                if t["severity"] in {"Kritis", "Critical"} and t["sla"] == "72h"]


def test_bug_signature_is_distinguishable_from_a_deliberate_72h():
    """Migration c8d5e2f14a90 keys off this exact pair.

    The old create endpoint always wrote sla="72h" together with
    escalation_level="Normal"; a real operator choice carries a severity label
    there instead.  If a future change makes "Normal" a valid severity, the
    migration's discriminator silently stops working — hence this guard.
    """
    assert "normal" not in ticketing.SEVERITY_POLICY
    assert "Normal" not in ticketing.SEVERITY_CANONICAL.values()
    # And a Kritis parent now yields a 4h child, so the pair cannot recur.
    assert ticketing.sla_label(ticketing.policy_for("Kritis")) == "4h"


def test_legacy_ticket_dict_without_new_fields_still_evaluates():
    """Rows written before this change must not crash the SLA engine."""
    legacy = {"id": "old", "case_id": "case-001", "status": "Sedang Ditinjau",
              "sla": "72h", "assigned_unit": "Unit Lama"}
    state = ticketing.sla_state(legacy)
    assert state["sla_state"] == "unknown"  # no due date -> not a false breach
    summary = ticketing.summarise([legacy])
    assert summary["total"] == 1 and summary["unassigned"] == 1
