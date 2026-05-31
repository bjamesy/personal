"""add calendar subscriptions

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str = "0011"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "calendar_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_calendar_subscriptions_token", "calendar_subscriptions", ["token"])

    op.create_table(
        "calendar_subscription_theatres",
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["subscription_id"],
            ["calendar_subscriptions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["theatre_id"], ["theatres.id"]),
        sa.PrimaryKeyConstraint("subscription_id", "theatre_id"),
    )


def downgrade() -> None:
    op.drop_table("calendar_subscription_theatres")
    op.drop_index("ix_calendar_subscriptions_token", table_name="calendar_subscriptions")
    op.drop_table("calendar_subscriptions")
