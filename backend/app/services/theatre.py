import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theatre import Theatre
from app.repositories.theatre import TheatreRepository
from app.schemas.theatre import TheatreResponse


class TheatreService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = TheatreRepository(session)

    async def get_all(self) -> list[TheatreResponse]:
        rows = await self.repository.get_all_with_last_scraped()
        return [
            TheatreResponse(
                id=theatre.id,
                name=theatre.name,
                slug=theatre.slug,
                source_url=theatre.source_url,
                is_cron_enabled=theatre.is_cron_enabled,
                last_scraped_at=last_scraped_at,
            )
            for theatre, last_scraped_at in rows
        ]

    async def get_by_id(self, theatre_id: uuid.UUID) -> Theatre | None:
        return await self.repository.get_by_id(theatre_id)
