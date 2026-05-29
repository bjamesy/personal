from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movie import Movie


class MovieRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_title(self, title: str) -> Movie | None:
        result = await self.session.execute(
            select(Movie).where(Movie.title == title)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, title: str) -> Movie:
        # Single round-trip, race-safe: insert and return the row, or fetch if it existed.
        stmt = (
            pg_insert(Movie)
            .values(title=title)
            .on_conflict_do_nothing(index_elements=["title"])
            .returning(Movie)
        )
        result = await self.session.execute(stmt)
        movie = result.scalar_one_or_none()
        if movie is None:
            # Conflict: row already existed — fetch it.
            result = await self.session.execute(
                select(Movie).where(Movie.title == title)
            )
            movie = result.scalar_one()
        return movie
