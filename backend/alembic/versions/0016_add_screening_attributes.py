"""add screening_attributes and screening_attribute_map tables

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0016"
down_revision: str = "0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "screening_attributes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "slug", name="uq_screening_attributes_category_slug"),
    )

    op.create_table(
        "screening_attribute_map",
        sa.Column("screening_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attribute_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["screening_id"], ["screenings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["attribute_id"], ["screening_attributes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("screening_id", "attribute_id"),
    )


def downgrade() -> None:
    op.drop_table("screening_attribute_map")
    op.drop_table("screening_attributes")
