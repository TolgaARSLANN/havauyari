"""Ölçümler ve toplama işi çalışmaları: measurements, runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-15

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "measurements",
        sa.Column("station", sa.String(64), sa.ForeignKey("stations.slug"), primary_key=True),
        sa.Column("time", TZ, primary_key=True),
        sa.Column("pm25", sa.Float(), nullable=False),
        sa.Column("updated_at", TZ, server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("started_at", TZ, nullable=False),
        sa.Column("finished_at", TZ, nullable=False),
        sa.Column("issued_at", TZ, nullable=False),
        sa.Column("ok", sa.Integer(), nullable=False),
        sa.Column("failed", sa.Integer(), nullable=False),
        sa.Column("measurements", sa.Integer(), nullable=False),
        sa.Column("errors", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("runs")
    op.drop_table("measurements")
