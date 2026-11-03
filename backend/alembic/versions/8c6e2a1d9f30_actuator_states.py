"""actuator states

Revision ID: 8c6e2a1d9f30
Revises: 6b9fe8d142ac
Create Date: 2026-11-03 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8c6e2a1d9f30"
down_revision: str | None = "6b9fe8d142ac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "actuator_states",
        sa.Column("device_id", sa.UUID(), nullable=False),
        sa.Column(
            "state",
            sa.String(length=32),
            server_default=sa.text("'idle'"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state IN ('off', 'idle', 'running', 'error', 'maintenance')",
            name="ck_actuator_states_state",
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            name="fk_actuator_states_device_id_devices",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.execute(
        """
        INSERT INTO actuator_states (device_id, state)
        SELECT id, 'idle'
        FROM devices
        WHERE role = 'actuator'
        ON CONFLICT (device_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("actuator_states")
