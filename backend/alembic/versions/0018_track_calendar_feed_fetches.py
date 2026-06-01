"""track calendar feed fetch count and last fetched timestamp

Revision ID: 0018
Revises: 0017
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0018"
down_revision: str = "0017"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column("calendar_subscriptions", sa.Column("fetch_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("calendar_subscriptions", sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("calendar_subscriptions", "last_fetched_at")
    op.drop_column("calendar_subscriptions", "fetch_count")
