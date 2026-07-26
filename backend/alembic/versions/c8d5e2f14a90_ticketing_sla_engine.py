"""ticketing SLA engine: severity, ownership, and due-date columns.

Additive only.  Existing tickets keep their ``sla`` label and are backfilled
onto the policy/due-date model in place:

- ``sla_policy`` is derived from the stored label ("24h" -> P1 ... "72h" -> P4)
  so a ticket that was genuinely a 72h item stays one.
- ``severity`` copies ``escalation_level``, which is where the seed loader had
  been putting the case priority.
- ``due_at`` is computed as created_at + policy hours for rows that lack one.
- ``resolved_at`` is set to ``updated_at`` for tickets already in a terminal
  status, so historical SLA compliance is judged against the completion time
  rather than being reported as an open breach.

Two classes of existing ticket are treated differently on purpose:

- Rows the *bug* produced — the old create endpoint always wrote sla="72h"
  together with escalation_level="Normal", so that exact pair marks an SLA
  nobody actually chose.  These are re-derived from the parent case severity,
  because leaving a Kritis case with a 72h child is the reported defect.
- Rows with a real escalation_level — seeded or operator-set.  Their stored
  SLA is preserved even where it looks tight, since silently shortening live
  deadlines would manufacture a wave of retroactive breaches.  These stay
  visible as-is; an operator can re-derive one by PATCHing its severity.

Legacy statuses outside the lifecycle are mapped onto it, otherwise the state
machine would have no transition out of them.
"""

from alembic import op
import sqlalchemy as sa

revision = "c8d5e2f14a90"
down_revision = "b4e1d9f27c33"
branch_labels = None
depends_on = None

_NEW_COLUMNS = (
    ("description", sa.Text()),
    ("severity", sa.String()),
    ("impact", sa.String()),
    ("urgency", sa.String()),
    ("sla_policy", sa.String()),
    ("assignee", sa.String()),
    ("assignment_group", sa.String()),
    ("category", sa.String()),
)


def upgrade() -> None:
    with op.batch_alter_table("tickets") as batch:
        for name, type_ in _NEW_COLUMNS:
            batch.add_column(sa.Column(name, type_, nullable=True))
        batch.add_column(sa.Column("labels", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("notes", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))

    # Backfill. Ordered longest-first so "72h" is not matched by a "2h" rule.
    op.execute("""
        UPDATE tickets SET sla_policy = CASE
            WHEN sla = '4h'  THEN 'P1'
            WHEN sla = '24h' THEN 'P2'
            WHEN sla = '48h' THEN 'P3'
            WHEN sla = '72h' THEN 'P4'
            ELSE 'P3'
        END WHERE sla_policy IS NULL
    """)
    # escalation_level held the case priority, except on rows created by the
    # old endpoint that hardcoded "Normal" — not a severity.  Those inherit
    # from the parent case instead, which is what should have happened when
    # they were created.
    op.execute("""
        UPDATE tickets SET severity = escalation_level
        WHERE severity IS NULL
          AND escalation_level IN ('Kritis', 'Critical', 'Tinggi', 'High',
                                   'Sedang', 'Medium', 'Rendah', 'Low')
    """)
    op.execute("""
        UPDATE tickets t SET severity = COALESCE(c.severity, c.priority_label)
        FROM cases c WHERE c.case_id = t.case_id AND t.severity IS NULL
    """)
    op.execute("UPDATE tickets SET assignment_group = assigned_unit WHERE assignment_group IS NULL")

    # Statuses outside the lifecycle would be unmovable: the state machine has
    # no transitions out of an unknown status.  Map the one legacy value in
    # use onto its lifecycle equivalent.
    op.execute("UPDATE tickets SET status = 'Sedang Ditinjau' WHERE status = 'Eskalasi'")
    # Correct the tickets the bug actually produced.  The old create endpoint
    # hardcoded sla="72h" AND escalation_level="Normal" together, so that exact
    # pair identifies a ticket whose SLA was never chosen by anyone.  Those are
    # re-derived from the parent case severity.  A 72h ticket that carries a
    # real escalation_level was a deliberate call and is left alone.
    op.execute("""
        UPDATE tickets t SET sla_policy = CASE
            WHEN COALESCE(c.severity, c.priority_label) IN ('Kritis', 'Critical') THEN 'P1'
            WHEN COALESCE(c.severity, c.priority_label) IN ('Tinggi', 'High')     THEN 'P2'
            WHEN COALESCE(c.severity, c.priority_label) IN ('Rendah', 'Low')      THEN 'P4'
            ELSE 'P3'
        END
        FROM cases c
        WHERE c.case_id = t.case_id
          AND t.sla = '72h' AND t.escalation_level = 'Normal'
    """)
    op.execute("""
        UPDATE tickets SET sla = CASE sla_policy
            WHEN 'P1' THEN '4h' WHEN 'P2' THEN '24h'
            WHEN 'P3' THEN '48h' ELSE '72h'
        END WHERE escalation_level = 'Normal'
    """)

    op.execute("""
        UPDATE tickets SET due_at = created_at + (CASE sla_policy
            WHEN 'P1' THEN INTERVAL '4 hours'
            WHEN 'P2' THEN INTERVAL '24 hours'
            WHEN 'P3' THEN INTERVAL '48 hours'
            ELSE INTERVAL '72 hours'
        END) WHERE due_at IS NULL
    """)
    op.execute("""
        UPDATE tickets SET resolved_at = updated_at
        WHERE resolved_at IS NULL AND status IN ('Selesai', 'Ditutup', 'Dibatalkan')
    """)


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch:
        for name in ("resolved_at", "notes", "labels"):
            batch.drop_column(name)
        for name, _ in reversed(_NEW_COLUMNS):
            batch.drop_column(name)
