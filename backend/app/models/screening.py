from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.screening_attribute import ScreeningAttribute, screening_attribute_map

if TYPE_CHECKING:
    from app.models.movie import Movie
    from app.models.theatre import Theatre


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    theatre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theatres.id"))
    movie_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("movies.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)
    raw_source_ref: Mapped[str | None] = mapped_column(String)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    theatre: Mapped[Theatre] = relationship(back_populates="screenings")
    movie: Mapped[Movie] = relationship(back_populates="screenings")
    attributes: Mapped[list[ScreeningAttribute]] = relationship(
        secondary=screening_attribute_map,
        lazy="raise",
    )
