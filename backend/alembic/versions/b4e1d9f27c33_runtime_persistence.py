"""runtime persistence: operator-mutable fields and seed provenance.

Additive only.  Adds the columns the runtime workflow already writes on the
dict layer (location/vendor override on cases, attachment + reviewer note on
signals, unlink flag on evidence) plus `is_seeded`/`seed_group` so a reset can
tell baseline rows from operator-created ones.

`audit_events.case_id` becomes nullable: review/defer actions record an event
before any case exists.
"""

from alembic import op
import sqlalchemy as sa

revision = "b4e1d9f27c33"
down_revision = "9c3f2ab7c1d0"
branch_labels = None
depends_on = None

# (table, column, type) for the seed-provenance pair added to every table a
# reset has to distinguish rows in.
_SEEDED_TABLES = ("vendors", "cases", "signals", "evidence", "risk_assessments",
                  "tickets", "audit_events")


def upgrade() -> None:
    with op.batch_alter_table("cases") as batch:
        batch.add_column(sa.Column("region", sa.String(), nullable=True))
        batch.add_column(sa.Column("district", sa.String(), nullable=True))
        batch.add_column(sa.Column("vendor_name_override", sa.String(), nullable=True))
        batch.add_column(sa.Column("vendor_source_note", sa.Text(), nullable=True))
        batch.add_column(sa.Column("assigned_investigator", sa.String(), nullable=True))
        batch.add_column(sa.Column("assigned_unit", sa.String(), nullable=True))
        batch.add_column(sa.Column("severity", sa.String(), nullable=True))

    with op.batch_alter_table("signals") as batch:
        batch.add_column(sa.Column("attachment_path", sa.String(), nullable=True))
        batch.add_column(sa.Column("attachment_title", sa.String(), nullable=True))
        batch.add_column(sa.Column("attachment_source", sa.String(), nullable=True))
        batch.add_column(sa.Column("attachment_note", sa.Text(), nullable=True))
        batch.add_column(sa.Column("reviewer_note", sa.Text(), nullable=True))

    with op.batch_alter_table("evidence") as batch:
        batch.add_column(sa.Column("unlinked_from_case", sa.Boolean(),
                                   nullable=False, server_default=sa.false()))

    # Audit events precede case creation during signal review.
    op.alter_column("audit_events", "case_id", existing_type=sa.String(), nullable=True)

    for table in _SEEDED_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("is_seeded", sa.Boolean(), nullable=False,
                                       server_default=sa.true()))
            batch.add_column(sa.Column("seed_group", sa.String(), nullable=True,
                                       server_default="baseline"))


def downgrade() -> None:
    for table in _SEEDED_TABLES:
        with op.batch_alter_table(table) as batch:
            batch.drop_column("seed_group")
            batch.drop_column("is_seeded")

    op.alter_column("audit_events", "case_id", existing_type=sa.String(), nullable=False)

    with op.batch_alter_table("evidence") as batch:
        batch.drop_column("unlinked_from_case")

    with op.batch_alter_table("signals") as batch:
        for name in ("reviewer_note", "attachment_note", "attachment_source",
                     "attachment_title", "attachment_path"):
            batch.drop_column(name)

    with op.batch_alter_table("cases") as batch:
        for name in ("severity", "assigned_unit", "assigned_investigator",
                     "vendor_source_note", "vendor_name_override", "district", "region"):
            batch.drop_column(name)
