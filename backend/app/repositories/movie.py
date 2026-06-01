from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, title: str, slug: str) -> Movie:
        stmt = (
            pg_insert(Movie)
            .values(title=title, slug=slug)
            .on_conflict_do_update(index_elements=["slug"], set_={"title": title})
            .returning(Movie)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
