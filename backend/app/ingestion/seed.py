from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.theatre import TheatreRepository
from app.scrapers.theatres import SCRAPERS


async def seed_theatres(session: AsyncSession) -> None:
    """Ensure a Theatre row exists for every registered scraper."""
    repo = TheatreRepository(session)
    for slug, scraper in SCRAPERS.items():
        existing = await repo.get_by_slug(slug)
        if not existing:
            await repo.create(
                name=scraper.config.name,
                slug=slug,
                source_url=scraper.config.source_url,
            )
    await session.commit()
