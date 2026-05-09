"""add todo_state table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-09 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "todo_state",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("last_status", sa.String(), nullable=False),
        sa.Column("open_group_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("run_id", "content"),
    )


def downgrade() -> None:
    op.drop_table("todo_state")
