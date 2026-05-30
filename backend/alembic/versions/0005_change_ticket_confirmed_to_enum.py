"""change ticket_confirmed to enum

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None

ticket_confirmed_status = sa.Enum("yes", "no", "not_yet", name="ticket_confirmed_status")


def upgrade() -> None:
    ticket_confirmed_status.create(op.get_bind())
    op.alter_column(
        "outbound_clicks",
        "ticket_confirmed",
        existing_type=sa.Boolean(),
        type_=ticket_confirmed_status,
        existing_nullable=True,
        postgresql_using="NULL::ticket_confirmed_status",
    )


def downgrade() -> None:
    op.alter_column(
        "outbound_clicks",
        "ticket_confirmed",
        existing_type=ticket_confirmed_status,
        type_=sa.Boolean(),
        existing_nullable=True,
        postgresql_using="NULL::boolean",
    )
    ticket_confirmed_status.drop(op.get_bind())
