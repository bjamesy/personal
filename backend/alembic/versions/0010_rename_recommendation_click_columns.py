"""rename recommendation click columns to google_ prefix and add metadata

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.alter_column(
        "restaurant_recommendation_clicks",
        "restaurant_name",
        new_column_name="google_restaurant_name",
    )
    op.alter_column(
        "restaurant_recommendation_clicks",
        "place_id",
        new_column_name="google_place_id",
    )
    op.add_column(
        "restaurant_recommendation_clicks",
        sa.Column("google_place_metadata", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("restaurant_recommendation_clicks", "google_place_metadata")
    op.alter_column(
        "restaurant_recommendation_clicks",
        "google_place_id",
        new_column_name="place_id",
    )
    op.alter_column(
        "restaurant_recommendation_clicks",
        "google_restaurant_name",
        new_column_name="restaurant_name",
    )
