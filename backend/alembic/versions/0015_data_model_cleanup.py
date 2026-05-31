"""data model cleanup: remove redundant theatre_ids, rename columns for clarity

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0015"
down_revision: str = "0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # --- Remove redundant theatre_id from outbound_clicks ---
    # Derivable via screening_id -> screenings.theatre_id
    op.drop_constraint("outbound_clicks_theatre_id_fkey", "outbound_clicks", type_="foreignkey")
    op.drop_column("outbound_clicks", "theatre_id")

    # --- Remove redundant theatre_id from restaurant_interest_events ---
    # Derivable via outbound_click_id -> outbound_clicks -> screening -> theatre
    op.drop_constraint("restaurant_interest_events_theatre_id_fkey", "restaurant_interest_events", type_="foreignkey")
    op.drop_column("restaurant_interest_events", "theatre_id")

    # --- Rename scraper_runs columns for clarity ---
    op.alter_column("scraper_runs", "screenings_found", new_column_name="screenings_scraped")
    op.alter_column("scraper_runs", "items_extracted", new_column_name="screenings_inserted")

    # --- Remove google_ vendor prefix from restaurant_recommendation_clicks ---
    op.alter_column("restaurant_recommendation_clicks", "google_restaurant_name", new_column_name="restaurant_name")
    op.alter_column("restaurant_recommendation_clicks", "google_place_id", new_column_name="place_id")
    op.alter_column("restaurant_recommendation_clicks", "google_place_metadata", new_column_name="place_metadata")

    # --- Normalise timestamp column naming: clicked_at -> created_at ---
    op.alter_column("outbound_clicks", "clicked_at", new_column_name="created_at")
    op.alter_column("restaurant_recommendation_clicks", "clicked_at", new_column_name="created_at")

    # --- Add outbound_click_id FK to restaurant_recommendation_clicks ---
    # Links recommendation clicks back to the interest event chain for funnel analysis
    op.add_column(
        "restaurant_recommendation_clicks",
        sa.Column("outbound_click_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "restaurant_recommendation_clicks_outbound_click_id_fkey",
        "restaurant_recommendation_clicks",
        "outbound_clicks",
        ["outbound_click_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("restaurant_recommendation_clicks_outbound_click_id_fkey", "restaurant_recommendation_clicks", type_="foreignkey")
    op.drop_column("restaurant_recommendation_clicks", "outbound_click_id")

    op.alter_column("restaurant_recommendation_clicks", "created_at", new_column_name="clicked_at")
    op.alter_column("outbound_clicks", "created_at", new_column_name="clicked_at")

    op.alter_column("restaurant_recommendation_clicks", "place_metadata", new_column_name="google_place_metadata")
    op.alter_column("restaurant_recommendation_clicks", "place_id", new_column_name="google_place_id")
    op.alter_column("restaurant_recommendation_clicks", "restaurant_name", new_column_name="google_restaurant_name")

    op.alter_column("scraper_runs", "screenings_inserted", new_column_name="items_extracted")
    op.alter_column("scraper_runs", "screenings_scraped", new_column_name="screenings_found")

    op.add_column("restaurant_interest_events", sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("restaurant_interest_events_theatre_id_fkey", "restaurant_interest_events", "theatres", ["theatre_id"], ["id"])

    op.add_column("outbound_clicks", sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("outbound_clicks_theatre_id_fkey", "outbound_clicks", "theatres", ["theatre_id"], ["id"])
