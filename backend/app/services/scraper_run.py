from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scraper_run import ScraperRun
from app.repositories.scraper_run import ScraperRunRepository


class ScraperRunService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ScraperRunRepository(session)

    async def get_latest_per_theatre(self) -> list[ScraperRun]:
        return await self.repository.get_latest_per_theatre()
