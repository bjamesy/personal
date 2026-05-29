from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.scraper_run import ScraperRun
    from app.models.screening import Screening


class Theatre(Base):
    __tablename__ = "theatres"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True)
    source_url: Mapped[str] = mapped_column(String)

    screenings: Mapped[list[Screening]] = relationship(back_populates="theatre")
    scraper_runs: Mapped[list[ScraperRun]] = relationship(back_populates="theatre")
