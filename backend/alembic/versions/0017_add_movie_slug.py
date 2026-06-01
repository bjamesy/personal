"""add slug column to movies, move unique constraint from title to slug

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-01
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0017"
down_revision: str = "0016"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Add slug, backfill from title (which currently holds the normalized form), then constrain.
    op.add_column("movies", sa.Column("slug", sa.String(), nullable=True))
    op.execute("UPDATE movies SET slug = title")
    op.alter_column("movies", "slug", nullable=False)
    op.create_unique_constraint("uq_movies_slug", "movies", ["slug"])
    op.drop_constraint("movies_title_key", "movies", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("movies_title_key", "movies", ["title"])
    op.drop_constraint("uq_movies_slug", "movies", type_="unique")
    op.drop_column("movies", "slug")
