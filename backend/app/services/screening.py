from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening import Screening
from app.repositories.screening import ScreeningRepository


class ScreeningService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = ScreeningRepository(session)

    async def get_by_month(self, year: int, month: int) -> list[Screening]:
        return await self.repository.get_by_month(year, month)

    async def get_upcoming(self) -> list[Screening]:
        return await self.repository.get_upcoming()
