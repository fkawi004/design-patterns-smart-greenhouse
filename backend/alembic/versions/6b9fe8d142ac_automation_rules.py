"""automation rules

Revision ID: 6b9fe8d142ac
Revises: a27bf23d9b81
Create Date: 2026-10-13 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "6b9fe8d142ac"
down_revision: str | None = "a27bf23d9b81"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("location_id", sa.UUID(), nullable=False),
        sa.Column(
            "strategy_key",
            sa.String(length=32),
            server_default=sa.text("'conservative'"),
            nullable=False,
        ),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            name="fk_automation_rules_location_id_locations",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("location_id"),
    )
    op.execute(
        """
        INSERT INTO automation_rules (location_id, strategy_key, parameters)
        SELECT id, 'conservative', '{}'::jsonb
        FROM locations
        ON CONFLICT (location_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_table("automation_rules")
