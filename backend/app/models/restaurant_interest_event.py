from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.outbound_click import OutboundClick
    from app.models.theatre import Theatre


class RestaurantInterestType(str, enum.Enum):
    before_movie = "before_movie"
    after_movie = "after_movie"
    browsing = "browsing"
    declined = "declined"


class RestaurantInterestEvent(Base):
    __tablename__ = "restaurant_interest_events"
    __table_args__ = (UniqueConstraint("outbound_click_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    outbound_click_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("outbound_clicks.id"))
    theatre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theatres.id"))
    interest_type: Mapped[RestaurantInterestType] = mapped_column(
        Enum(RestaurantInterestType, name="restaurant_interest_type")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    outbound_click: Mapped[OutboundClick] = relationship()
    theatre: Mapped[Theatre] = relationship()
