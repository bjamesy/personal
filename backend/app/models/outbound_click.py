from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.screening import Screening
    from app.models.theatre import Theatre


class TicketConfirmedStatus(str, enum.Enum):
    yes = "yes"
    no = "no"
    not_yet = "not_yet"


class OutboundClick(Base):
    __tablename__ = "outbound_clicks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    screening_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("screenings.id"))
    theatre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theatres.id"))
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ticket_confirmed: Mapped[TicketConfirmedStatus | None] = mapped_column(
        Enum(TicketConfirmedStatus, name="ticket_confirmed_status")
    )
    prompted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    screening: Mapped[Screening] = relationship()
    theatre: Mapped[Theatre] = relationship()
