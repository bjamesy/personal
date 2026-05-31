from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

screening_attribute_map = Table(
    "screening_attribute_map",
    Base.metadata,
    Column("screening_id", ForeignKey("screenings.id", ondelete="CASCADE"), primary_key=True),
    Column("attribute_id", ForeignKey("screening_attributes.id", ondelete="CASCADE"), primary_key=True),
)


class ScreeningAttribute(Base):
    __tablename__ = "screening_attributes"
    __table_args__ = (
        UniqueConstraint("category", "slug", name="uq_screening_attributes_category_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
