"""
Scheduler worker — runs as a separate container (same image, different CMD).

Lifecycle:
  1. Seed theatre rows on startup (idempotent).
  2. Run the full scraping + ingestion pipeline immediately.
  3. Sleep for SCRAPE_INTERVAL_HOURS, then repeat.

The interval is measured from the END of each run, so a slow run does not
cause overlapping executions.
"""

import asyncio
import logging

from app.config import settings
from app.database import async_session_factory
from app.ingestion.seed import seed_theatres
from app.ingestion.service import ingest_all
from app.logging_config import setup_logging
from app.models.scraper_run import ScraperRunStatus
from app.repositories.scraper_run import ScraperRunRepository
from app.repositories.theatre import TheatreRepository
from app.scrapers.base import ScraperResult
from app.scrapers.runner import run_all_scrapers
from app.scrapers.theatres import get_all_scrapers

logger = logging.getLogger(__name__)

_CONSECUTIVE_FAILURE_THRESHOLD = 3


async def run_pipeline() -> None:
    logger.info("pipeline_start")
    scrapers = get_all_scrapers()
    logger.info("pipeline_scrapers", extra={"total": len(scrapers)})
    results = await run_all_scrapers(scrapers)
    async with async_session_factory() as session:
        await ingest_all(results, session)
        await _sync_scraper_health(results, session)
    logger.info("pipeline_complete", extra={"theatres": len(results)})


async def _sync_scraper_health(
    results: list[ScraperResult], session
) -> None:
    theatre_repo = TheatreRepository(session)
    run_repo = ScraperRunRepository(session)

    for result in results:
        theatre = await theatre_repo.get_by_slug(result.theatre_slug)
        if not theatre:
            continue

        if result.success and not theatre.is_cron_enabled:
            await theatre_repo.enable(result.theatre_slug)
            await session.commit()
            logger.info("scraper_auto_enabled", extra={"slug": result.theatre_slug})
            continue

        if not theatre.is_cron_enabled:
            continue

        recent = await run_repo.get_last_n_by_theatre(
            theatre.id, _CONSECUTIVE_FAILURE_THRESHOLD
        )
        if (
            len(recent) >= _CONSECUTIVE_FAILURE_THRESHOLD
            and all(r.status == ScraperRunStatus.failure for r in recent)
        ):
            await theatre_repo.disable(result.theatre_slug)
            await session.commit()
            logger.warning(
                "scraper_auto_disabled",
                extra={
                    "slug": result.theatre_slug,
                    "consecutive_failures": _CONSECUTIVE_FAILURE_THRESHOLD,
                },
            )


async def main() -> None:
    setup_logging()
    interval = settings.scrape_interval_hours * 3600
    logger.info("scheduler_start", extra={"interval_hours": settings.scrape_interval_hours})

    async with async_session_factory() as session:
        await seed_theatres(session)

    while True:
        try:
            await run_pipeline()
        except Exception:
            logger.exception("pipeline_error")
        logger.info("scheduler_sleeping", extra={"seconds": interval})
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())
