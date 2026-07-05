"""initial schema: runs (UNIQUE state_key), golden_sets, baselines

Revision ID: 0001
Revises:
Create Date: 2026-07-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("state_key", sa.Text(), nullable=False),
        sa.Column("run_json", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("state_key", name="uq_runs_state_key"),
    )
    op.create_table(
        "golden_sets",
        sa.Column("version", sa.String(), primary_key=True),
        sa.Column("gs_json", postgresql.JSONB(), nullable=False),
    )
    op.create_table(
        "baselines",
        sa.Column("version", sa.String(), primary_key=True),
        sa.Column("baseline_json", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("baselines")
    op.drop_table("golden_sets")
    op.drop_table("runs")
