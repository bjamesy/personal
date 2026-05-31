"""add screenings indexes on theatre_id+start_time and start_time

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-31
"""

from alembic import op

revision: str = "0013"
down_revision: str = "0012"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_index(
        "ix_screenings_theatre_id_start_time",
        "screenings",
        ["theatre_id", "start_time"],
    )
    op.create_index(
        "ix_screenings_start_time",
        "screenings",
        ["start_time"],
    )


def downgrade() -> None:
    op.drop_index("ix_screenings_start_time", table_name="screenings")
    op.drop_index("ix_screenings_theatre_id_start_time", table_name="screenings")
