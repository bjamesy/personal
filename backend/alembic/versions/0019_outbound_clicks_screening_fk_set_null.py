"""outbound_clicks screening_id FK: set null on delete

Revision ID: 0019
Revises: 0018
Create Date: 2026-06-03
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("outbound_clicks", "screening_id", nullable=True)
    op.drop_constraint("outbound_clicks_screening_id_fkey", "outbound_clicks", type_="foreignkey")
    op.create_foreign_key(
        "outbound_clicks_screening_id_fkey",
        "outbound_clicks",
        "screenings",
        ["screening_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("outbound_clicks_screening_id_fkey", "outbound_clicks", type_="foreignkey")
    op.create_foreign_key(
        "outbound_clicks_screening_id_fkey",
        "outbound_clicks",
        "screenings",
        ["screening_id"],
        ["id"],
    )
    op.alter_column("outbound_clicks", "screening_id", nullable=False)
