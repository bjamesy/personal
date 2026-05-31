"""add index on scraper_runs(theatre_id, started_at)

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-31
"""

from alembic import op

revision: str = "0014"
down_revision: str = "0013"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_index(
        "ix_scraper_runs_theatre_id_started_at",
        "scraper_runs",
        ["theatre_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_scraper_runs_theatre_id_started_at", table_name="scraper_runs")
