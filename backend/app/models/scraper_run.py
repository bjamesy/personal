from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.theatre import Theatre


class ScraperRunStatus(enum.Enum):
    success = "success"
    failure = "failure"


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    theatre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theatres.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ScraperRunStatus | None] = mapped_column(
        Enum(ScraperRunStatus, name="scraper_run_status")
    )
    items_extracted: Mapped[int | None] = mapped_column(Integer)
    screenings_found: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)

    theatre: Mapped[Theatre] = relationship(back_populates="scraper_runs")
