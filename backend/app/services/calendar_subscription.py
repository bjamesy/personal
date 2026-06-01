from __future__ import annotations

import uuid
from datetime import timedelta
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from icalendar import Calendar, Event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.calendar_subscription import CalendarSubscription
from app.repositories.calendar_subscription import CalendarSubscriptionRepository
from app.repositories.screening import ScreeningRepository

_TORONTO_TZ = ZoneInfo("America/Toronto")
_DEFAULT_DURATION = timedelta(hours=2)


def _ticket_url(raw_source_ref: str | None, theatre_source_url: str) -> str:
    if not raw_source_ref:
        return theatre_source_url
    if raw_source_ref.startswith("/"):
        origin = urlparse(theatre_source_url)
        base = f"{origin.scheme}://{origin.netloc}"
        return urljoin(base, raw_source_ref)
    return raw_source_ref


class CalendarSubscriptionService:
    def __init__(self, session: AsyncSession) -> None:
        self.subscription_repo = CalendarSubscriptionRepository(session)
        self.screening_repo = ScreeningRepository(session)

    async def create(
        self,
        theatre_ids: list[uuid.UUID],
        label: str | None = None,
    ) -> CalendarSubscription:
        try:
            subscription = await self.subscription_repo.create(theatre_ids, label)
            await self.subscription_repo.session.commit()
        except IntegrityError:
            await self.subscription_repo.session.rollback()
            raise HTTPException(status_code=422, detail="One or more theatre IDs are invalid")
        return subscription

    async def build_ics(self, token: str) -> bytes | None:
        subscription = await self.subscription_repo.get_by_token(token)
        if not subscription:
            return None

        await self.subscription_repo.record_fetch(subscription)
        await self.subscription_repo.session.commit()

        theatre_ids = [st.theatre_id for st in subscription.subscription_theatres]
        screenings = await self.screening_repo.get_upcoming_for_theatres(theatre_ids)

        cal = Calendar()
        cal.add("prodid", "-//Toronto Theatre Screenings//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname", subscription.label or "Toronto Theatre Screenings")
        cal.add("x-wr-caldesc", "Upcoming film screenings")
        cal.add("x-wr-timezone", "America/Toronto")

        for screening in screenings:
            dtstart = screening.start_time.astimezone(_TORONTO_TZ)
            if screening.end_time:
                dtend = screening.end_time.astimezone(_TORONTO_TZ)
            else:
                dtend = dtstart + _DEFAULT_DURATION

            ticket_url = _ticket_url(screening.raw_source_ref, screening.theatre.source_url)

            event = Event()
            event.add("uid", f"screening:{screening.idempotency_key}")
            event.add("summary", f"{screening.movie.title} @ {screening.theatre.name}")
            event.add("dtstart", dtstart)
            event.add("dtend", dtend)
            event.add("location", screening.theatre.name)
            event.add("url", ticket_url)
            description = f"Tickets: {ticket_url}"
            if settings.public_base_url:
                description += f"\n{settings.public_base_url.rstrip('/')}"
            event.add("description", description)
            cal.add_component(event)

        cal.add_missing_timezones()
        return cal.to_ical()
