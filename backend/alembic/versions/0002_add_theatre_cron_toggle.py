"""add is_cron_enabled to theatres

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "theatres",
        sa.Column(
            "is_cron_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("theatres", "is_cron_enabled")
