from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theatre import Theatre
from app.repositories.theatre import TheatreRepository


class TheatreService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = TheatreRepository(session)

    async def get_all(self) -> list[Theatre]:
        return await self.repository.get_all()
