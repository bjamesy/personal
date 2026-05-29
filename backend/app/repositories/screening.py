import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.screening import Screening


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
            .options(selectinload(Screening.theatre), selectinload(Screening.movie))
            .where(Screening.start_time >= start)
            .where(Screening.start_time < end)
            .order_by(Screening.start_time)
        )
        return list(result.scalars().all())

    async def get_upcoming(self) -> list[Screening]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Screening)
            .options(selectinload(Screening.theatre), selectinload(Screening.movie))
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

    async def delete_stale_future(
        self,
        theatre_id: uuid.UUID,
        current_keys: set[str],
        from_time: datetime,
    ) -> int:
        """Delete future screenings for a theatre that are no longer in the current scrape."""
        stmt = (
            delete(Screening)
            .where(Screening.theatre_id == theatre_id)
            .where(Screening.start_time >= from_time)
            .where(Screening.idempotency_key.notin_(current_keys))
        )
        result = await self.session.execute(stmt)
        return result.rowcount
