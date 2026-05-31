from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.restaurant_interest_event import RestaurantInterestType

if TYPE_CHECKING:
    from app.models.theatre import Theatre


class RestaurantRecommendationClick(Base):
    __tablename__ = "restaurant_recommendation_clicks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    theatre_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("theatres.id"))
    restaurant_name: Mapped[str] = mapped_column(Text)
    interest_type: Mapped[RestaurantInterestType] = mapped_column(
        Enum(RestaurantInterestType, name="restaurant_interest_type", create_type=False)
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    theatre: Mapped[Theatre] = relationship()
