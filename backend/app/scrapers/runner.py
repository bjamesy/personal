import asyncio
import logging
from datetime import datetime, timezone

from app.scrapers.base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)


async def run_scraper(scraper: BaseScraper) -> ScraperResult:
    slug = scraper.config.slug
    started_at = datetime.now(timezone.utc)
    logger.info("scraper_start", extra={"theatre": slug, "started_at": started_at.isoformat()})

    try:
        screenings = await scraper.scrape()
        ended_at = datetime.now(timezone.utc)
        logger.info(
            "scraper_success",
            extra={"theatre": slug, "items": len(screenings), "ended_at": ended_at.isoformat()},
        )
        return ScraperResult(
            theatre_slug=slug,
            started_at=started_at,
            ended_at=ended_at,
            success=True,
            screenings=screenings,
        )
    except Exception as exc:
        ended_at = datetime.now(timezone.utc)
        logger.error(
            "scraper_failure",
            extra={"theatre": slug, "error": str(exc), "ended_at": ended_at.isoformat()},
            exc_info=True,
        )
        return ScraperResult(
            theatre_slug=slug,
            started_at=started_at,
            ended_at=ended_at,
            success=False,
            error=str(exc),
        )


async def run_all_scrapers(scrapers: list[BaseScraper]) -> list[ScraperResult]:
    return list(await asyncio.gather(*[run_scraper(s) for s in scrapers]))
