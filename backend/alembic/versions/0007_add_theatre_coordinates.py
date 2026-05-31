"""add latitude and longitude to theatres

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-30
"""

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | None = None
depends_on: str | None = None

COORDINATES: dict[str, tuple[float, float]] = {
    "varsity":        (43.6690, -79.3876),
    "fox":            (43.6636, -79.2953),
    "hotdocs":        (43.6640, -79.4011),
    "imagine_carlton":(43.6600, -79.3797),
    "kingsway":       (43.6494, -79.5095),
    "paradise":       (43.6606, -79.4278),
    "revue":          (43.6491, -79.4476),
    "tiff":           (43.6472, -79.3901),
    "tops":           (43.6562, -79.3082),
}


def upgrade() -> None:
    op.add_column("theatres", sa.Column("latitude", sa.Double(), nullable=True))
    op.add_column("theatres", sa.Column("longitude", sa.Double(), nullable=True))

    conn = op.get_bind()
    for slug, (lat, lng) in COORDINATES.items():
        conn.execute(
            sa.text("UPDATE theatres SET latitude = :lat, longitude = :lng WHERE slug = :slug"),
            {"lat": lat, "lng": lng, "slug": slug},
        )


def downgrade() -> None:
    op.drop_column("theatres", "longitude")
    op.drop_column("theatres", "latitude")
