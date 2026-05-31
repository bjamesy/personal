"""replace theatre_id with screening_id on restaurant_recommendation_clicks

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "restaurant_recommendation_clicks",
        sa.Column("screening_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute("""
        UPDATE restaurant_recommendation_clicks rrc
        SET screening_id = (
            SELECT s.id FROM screenings s
            WHERE s.theatre_id = rrc.theatre_id
            LIMIT 1
        )
    """)
    op.alter_column("restaurant_recommendation_clicks", "screening_id", nullable=False)
    op.drop_constraint(
        "restaurant_recommendation_clicks_theatre_id_fkey",
        "restaurant_recommendation_clicks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "restaurant_recommendation_clicks_screening_id_fkey",
        "restaurant_recommendation_clicks",
        "screenings",
        ["screening_id"],
        ["id"],
    )
    op.drop_column("restaurant_recommendation_clicks", "theatre_id")


def downgrade() -> None:
    op.add_column(
        "restaurant_recommendation_clicks",
        sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute("""
        UPDATE restaurant_recommendation_clicks rrc
        SET theatre_id = (
            SELECT s.theatre_id FROM screenings s
            WHERE s.id = rrc.screening_id
        )
    """)
    op.alter_column("restaurant_recommendation_clicks", "theatre_id", nullable=False)
    op.drop_constraint(
        "restaurant_recommendation_clicks_screening_id_fkey",
        "restaurant_recommendation_clicks",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "restaurant_recommendation_clicks_theatre_id_fkey",
        "restaurant_recommendation_clicks",
        "theatres",
        ["theatre_id"],
        ["id"],
    )
    op.drop_column("restaurant_recommendation_clicks", "screening_id")
