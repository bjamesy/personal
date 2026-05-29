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
from app.scrapers.runner import run_all_scrapers
from app.scrapers.theatres import get_all_scrapers

logger = logging.getLogger(__name__)


async def run_pipeline() -> None:
    logger.info("pipeline_start")
    scrapers = get_all_scrapers()
    results = await run_all_scrapers(scrapers)
    async with async_session_factory() as session:
        await ingest_all(results, session)
    logger.info("pipeline_complete", extra={"theatres": len(results)})


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
