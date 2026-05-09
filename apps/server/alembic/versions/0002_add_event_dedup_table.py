"""add event_dedup table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-09 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_dedup",
        sa.Column("event_key", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("event_key"),
    )


def downgrade() -> None:
    op.drop_table("event_dedup")
