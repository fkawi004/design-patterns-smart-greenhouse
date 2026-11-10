"""actuator execution log

Revision ID: 9d4f7c2b8a61
Revises: 8c6e2a1d9f30
Create Date: 2026-11-10 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "9d4f7c2b8a61"
down_revision: str | None = "8c6e2a1d9f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "actuator_execution_log",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column(
            "policy_applied",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            name="fk_actuator_execution_log_device_id_devices",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_actuator_execution_log_created_at",
        "actuator_execution_log",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_actuator_execution_log_created_at",
        table_name="actuator_execution_log",
    )
    op.drop_table("actuator_execution_log")
