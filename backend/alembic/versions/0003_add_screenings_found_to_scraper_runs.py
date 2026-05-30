"""add screenings_found to scraper_runs

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "scraper_runs",
        sa.Column("screenings_found", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scraper_runs", "screenings_found")
