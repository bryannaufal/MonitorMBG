"""case-centric workflow fields and one-to-many child tickets.

The migration is additive for cases.  Existing ticket rows retain their
case_id and become the first child workstream; no case or ticket is dropped.
"""

from alembic import op
import sqlalchemy as sa

revision = "9c3f2ab7c1d0"
down_revision = "5a7a76a52406"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("cases") as batch:
        batch.add_column(sa.Column("case_type", sa.String(), nullable=True))
        batch.add_column(sa.Column("case_subtype", sa.String(), nullable=True))
        batch.add_column(sa.Column("impact_summary", sa.Text(), nullable=True))
        batch.add_column(sa.Column("primary_owner", sa.String(), nullable=True))
        batch.add_column(sa.Column("handling_team", sa.String(), nullable=True))
        batch.add_column(sa.Column("secondary_owner", sa.String(), nullable=True))
        batch.add_column(sa.Column("watchers", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("handling_strategy", sa.String(), nullable=True))
        batch.add_column(sa.Column("related_case_id", sa.String(), nullable=True))
        batch.add_column(sa.Column("case_relationship", sa.String(), nullable=True))
        batch.add_column(sa.Column("blockers", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("resolution_summary", sa.Text(), nullable=True))
    with op.batch_alter_table("tickets") as batch:
        batch.drop_constraint("tickets_case_id_key", type_="unique")
        batch.add_column(sa.Column("workstream", sa.String(), nullable=True))
        batch.add_column(sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch:
        batch.drop_column("due_at")
        batch.drop_column("workstream")
        batch.create_unique_constraint("tickets_case_id_key", ["case_id"])
    with op.batch_alter_table("cases") as batch:
        for name in ("resolution_summary", "blockers", "case_relationship", "related_case_id", "handling_strategy", "due_at", "watchers", "secondary_owner", "handling_team", "primary_owner", "impact_summary", "case_subtype", "case_type"):
            batch.drop_column(name)
