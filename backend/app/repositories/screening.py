import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.screening import Screening
from app.models.screening_attribute import screening_attribute_map


class ScreeningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_month(self, year: int, month: int) -> list[Screening]:
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1

        start = datetime(year, month, 1, tzinfo=timezone.utc)
        end = datetime(next_year, next_month, 1, tzinfo=timezone.utc)

        result = await self.session.execute(
            select(Screening)
            .options(
                selectinload(Screening.theatre),
                selectinload(Screening.movie),
                selectinload(Screening.attributes),
            )
            .where(Screening.start_time >= start)
            .where(Screening.start_time < end)
            .order_by(Screening.start_time)
        )
        return list(result.scalars().all())

    async def get_upcoming(self) -> list[Screening]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Screening)
            .options(
                selectinload(Screening.theatre),
                selectinload(Screening.movie),
                selectinload(Screening.attributes),
            )
            .where(Screening.start_time >= now)
            .order_by(Screening.start_time)
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        theatre_id: uuid.UUID,
        movie_id: uuid.UUID,
        start_time: datetime,
        idempotency_key: str,
        end_time: datetime | None = None,
        raw_source_ref: str | None = None,
        raw_data: dict | None = None,
    ) -> int:
        """Insert the screening. Returns 1 if inserted, 0 if it already existed."""
        stmt = pg_insert(Screening).values(
            theatre_id=theatre_id,
            movie_id=movie_id,
            start_time=start_time,
            end_time=end_time,
            idempotency_key=idempotency_key,
            raw_source_ref=raw_source_ref,
            raw_data=raw_data,
        ).on_conflict_do_nothing(index_elements=["idempotency_key"])
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_by_idempotency_key(self, key: str) -> Screening | None:
        result = await self.session.execute(
            select(Screening).where(Screening.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def sync_attributes(self, screening_id: uuid.UUID, attribute_ids: list[uuid.UUID]) -> None:
        await self.session.execute(
            delete(screening_attribute_map).where(
                screening_attribute_map.c.screening_id == screening_id
            )
        )
        if attribute_ids:
            await self.session.execute(
                screening_attribute_map.insert(),
                [{"screening_id": screening_id, "attribute_id": aid} for aid in attribute_ids],
            )

    async def delete_stale_future(
        self,
        theatre_id: uuid.UUID,
        current_keys: set[str],
        from_time: datetime,
        to_time: datetime | None = None,
    ) -> int:
        """Delete screenings for a theatre within [from_time, to_time] not in the current scrape.

        Passing to_time ensures we don't touch screenings beyond the scrape window — only
        screenings the scraper actually looked at are considered candidates for deletion.
        """
        stmt = (
            delete(Screening)
            .where(Screening.theatre_id == theatre_id)
            .where(Screening.start_time >= from_time)
            .where(Screening.idempotency_key.notin_(current_keys))
        )
        if to_time is not None:
            stmt = stmt.where(Screening.start_time <= to_time)
        result = await self.session.execute(stmt)
        return result.rowcount

    async def get_upcoming_for_theatres(
        self, theatre_ids: list[uuid.UUID], days_ahead: int = 90
    ) -> list[Screening]:
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days_ahead)
        result = await self.session.execute(
            select(Screening)
            .options(selectinload(Screening.theatre), selectinload(Screening.movie))
            .where(Screening.theatre_id.in_(theatre_ids))
            .where(Screening.start_time >= now)
            .where(Screening.start_time <= cutoff)
            .order_by(Screening.start_time)
        )
        return list(result.scalars().all())
