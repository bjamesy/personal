"""add restaurant_interest_events table

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None

restaurant_interest_type = sa.Enum(
    "before_movie", "after_movie", "browsing", "declined",
    name="restaurant_interest_type",
)


def upgrade() -> None:
    op.create_table(
        "restaurant_interest_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outbound_click_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interest_type", restaurant_interest_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["outbound_click_id"], ["outbound_clicks.id"]),
        sa.ForeignKeyConstraint(["theatre_id"], ["theatres.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("outbound_click_id"),
    )


def downgrade() -> None:
    op.drop_table("restaurant_interest_events")
    restaurant_interest_type.drop(op.get_bind())
