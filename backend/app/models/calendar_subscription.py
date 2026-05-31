from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.theatre import Theatre


class CalendarSubscription(Base):
    __tablename__ = "calendar_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(Text, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    label: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    subscription_theatres: Mapped[list[CalendarSubscriptionTheatre]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )


class CalendarSubscriptionTheatre(Base):
    __tablename__ = "calendar_subscription_theatres"

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("calendar_subscriptions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    theatre_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("theatres.id"),
        primary_key=True,
    )

    subscription: Mapped[CalendarSubscription] = relationship(
        back_populates="subscription_theatres"
    )
    theatre: Mapped[Theatre] = relationship()
