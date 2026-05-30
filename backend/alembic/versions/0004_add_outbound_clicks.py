"""add outbound_clicks table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "outbound_clicks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("screening_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("theatre_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "clicked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ticket_confirmed", sa.Boolean(), nullable=True),
        sa.Column("prompted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["screening_id"], ["screenings.id"]),
        sa.ForeignKeyConstraint(["theatre_id"], ["theatres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("outbound_clicks")
