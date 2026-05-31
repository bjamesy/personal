"""add restaurant_recommendation_clicks table

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "restaurant_recommendation_clicks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("restaurant_name", sa.Text(), nullable=False),
        sa.Column(
            "interest_type",
            postgresql.ENUM("before_movie", "after_movie", "browsing", "declined",
                            name="restaurant_interest_type", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "clicked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["theatre_id"], ["theatres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("restaurant_recommendation_clicks")
