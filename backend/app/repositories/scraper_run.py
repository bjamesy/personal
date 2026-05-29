import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scraper_run import ScraperRun, ScraperRunStatus


class ScraperRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, theatre_id: uuid.UUID, started_at: datetime) -> ScraperRun:
        scraper_run = ScraperRun(theatre_id=theatre_id, started_at=started_at)
        self.session.add(scraper_run)
        await self.session.flush()
        return scraper_run

    async def complete(
        self,
        scraper_run_id: uuid.UUID,
        ended_at: datetime,
        status: ScraperRunStatus,
        items_extracted: int | None = None,
        error_message: str | None = None,
    ) -> ScraperRun:
        result = await self.session.execute(
            select(ScraperRun).where(ScraperRun.id == scraper_run_id)
        )
        scraper_run = result.scalar_one()
        scraper_run.ended_at = ended_at
        scraper_run.status = status
        scraper_run.items_extracted = items_extracted
        scraper_run.error_message = error_message
        await self.session.flush()
        return scraper_run

    async def get_latest_per_theatre(self) -> list[ScraperRun]:
        # DISTINCT ON (theatre_id) with ORDER BY started_at DESC gives latest run per theatre
        result = await self.session.execute(
            select(ScraperRun)
            .options(selectinload(ScraperRun.theatre))
            .distinct(ScraperRun.theatre_id)
            .order_by(ScraperRun.theatre_id, ScraperRun.started_at.desc())
        )
        return list(result.scalars().all())
