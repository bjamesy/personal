from __future__ import annotations

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.calendar_subscription import CalendarSubscription, CalendarSubscriptionTheatre


class CalendarSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        theatre_ids: list[uuid.UUID],
        label: str | None = None,
    ) -> CalendarSubscription:
        token = secrets.token_urlsafe(32)
        subscription = CalendarSubscription(token=token, label=label)
        self.session.add(subscription)
        await self.session.flush()

        for theatre_id in theatre_ids:
            self.session.add(
                CalendarSubscriptionTheatre(
                    subscription_id=subscription.id,
                    theatre_id=theatre_id,
                )
            )
        await self.session.flush()
        return subscription

    async def get_by_token(self, token: str) -> CalendarSubscription | None:
        result = await self.session.execute(
            select(CalendarSubscription)
            .options(
                selectinload(CalendarSubscription.subscription_theatres).selectinload(
                    CalendarSubscriptionTheatre.theatre
                )
            )
            .where(CalendarSubscription.token == token)
            .where(CalendarSubscription.is_active.is_(True))
        )
        return result.scalar_one_or_none()
