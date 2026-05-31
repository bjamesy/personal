from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.restaurant_interest_event import RestaurantInterestType

if TYPE_CHECKING:
    from app.models.screening import Screening


class RestaurantRecommendationClick(Base):
    __tablename__ = "restaurant_recommendation_clicks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    screening_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("screenings.id"))
    outbound_click_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("outbound_clicks.id"), nullable=True)
    restaurant_name: Mapped[str] = mapped_column(Text)
    interest_type: Mapped[RestaurantInterestType] = mapped_column(
        Enum(RestaurantInterestType, name="restaurant_interest_type", create_type=False)
    )
    place_id: Mapped[str | None] = mapped_column(String, nullable=True)
    place_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    screening: Mapped[Screening] = relationship()
