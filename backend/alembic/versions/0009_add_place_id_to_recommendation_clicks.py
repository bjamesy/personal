"""add place_id to restaurant_recommendation_clicks

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "restaurant_recommendation_clicks",
        sa.Column("place_id", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("restaurant_recommendation_clicks", "place_id")
