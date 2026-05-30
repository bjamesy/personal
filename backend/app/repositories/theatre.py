import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.theatre import Theatre


class TheatreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Theatre]:
        result = await self.session.execute(select(Theatre).order_by(Theatre.name))
        return list(result.scalars().all())

    async def get_by_id(self, theatre_id: uuid.UUID) -> Theatre | None:
        result = await self.session.execute(
            select(Theatre).where(Theatre.id == theatre_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Theatre | None:
        result = await self.session.execute(
            select(Theatre).where(Theatre.slug == slug)
        )
        return result.scalar_one_or_none()

    async def disable(self, slug: str) -> None:
        result = await self.session.execute(
            select(Theatre).where(Theatre.slug == slug)
        )
        theatre = result.scalar_one_or_none()
        if theatre:
            theatre.is_cron_enabled = False
            await self.session.flush()

    async def create(self, name: str, slug: str, source_url: str) -> Theatre:
        theatre = Theatre(name=name, slug=slug, source_url=source_url)
        self.session.add(theatre)
        await self.session.flush()
        return theatre
