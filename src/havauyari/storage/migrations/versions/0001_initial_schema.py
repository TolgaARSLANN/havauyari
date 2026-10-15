"""İlk şema: stations, forecasts, alerts

Revision ID: 0001
Revises:
Create Date: 2026-10-15

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "stations",
        sa.Column("slug", sa.String(64), primary_key=True),
        sa.Column("sim_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("city", sa.String(64), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("area_type", sa.String(64), nullable=True),
        sa.Column("source_type", sa.String(64), nullable=True),
        sa.Column("updated_at", TZ, server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "forecasts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("station", sa.String(64), sa.ForeignKey("stations.slug"), nullable=False),
        sa.Column("issued_at", TZ, nullable=False),
        sa.Column("target_time", TZ, nullable=False),
        sa.Column("pm25", sa.Float(), nullable=False),
        sa.Column("low_80", sa.Float(), nullable=False),
        sa.Column("high_80", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("station", "target_time", name="uq_forecasts_station_target"),
    )
    op.create_index("ix_forecasts_station", "forecasts", ["station"])
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("station", sa.String(64), sa.ForeignKey("stations.slug"), nullable=False),
        sa.Column("issued_at", TZ, nullable=False),
        sa.Column("target_time", TZ, nullable=False),
        sa.Column("pm25", sa.Float(), nullable=False),
        sa.Column("decision_threshold", sa.Float(), nullable=False),
        sa.Column("is_alert", sa.Boolean(), nullable=False),
        sa.Column("risk", sa.Boolean(), nullable=False),
        sa.Column("created_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZ, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("station", "target_time", name="uq_alerts_station_target"),
    )
    op.create_index("ix_alerts_station", "alerts", ["station"])


def downgrade() -> None:
    op.drop_index("ix_alerts_station", table_name="alerts")
    op.drop_table("alerts")
    op.drop_index("ix_forecasts_station", table_name="forecasts")
    op.drop_table("forecasts")
    op.drop_table("stations")
