import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.ingestion.normalizer import normalize_title
from app.models.scraper_run import ScraperRunStatus
from app.repositories.movie import MovieRepository
from app.repositories.scraper_run import ScraperRunRepository
from app.repositories.screening import ScreeningRepository
from app.repositories.screening_attribute import ScreeningAttributeRepository
from app.repositories.theatre import TheatreRepository
from app.scrapers.base import LOOKAHEAD_DAYS, ScraperResult

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.theatre_repo = TheatreRepository(session)
        self.movie_repo = MovieRepository(session)
        self.screening_repo = ScreeningRepository(session)
        self.attribute_repo = ScreeningAttributeRepository(session)
        self.scraper_run_repo = ScraperRunRepository(session)

    async def ingest(self, result: ScraperResult) -> None:
        theatre = await self.theatre_repo.get_by_slug(result.theatre_slug)
        if not theatre:
            logger.error(
                "ingest_theatre_not_found",
                extra={"slug": result.theatre_slug},
            )
            return

        scraper_run = await self.scraper_run_repo.create(
            theatre_id=theatre.id,
            started_at=result.started_at,
        )

        if not result.success:
            await self.scraper_run_repo.complete(
                scraper_run_id=scraper_run.id,
                ended_at=result.ended_at,
                status=ScraperRunStatus.failure,
                screenings_scraped=0,
                error_message=result.error,
            )
            await self.session.commit()
            return

        count = 0
        current_keys: set[str] = set()

        for raw in result.screenings:
            normalized = normalize_title(raw.movie_title)

            if not normalized:
                logger.warning(
                    "ingest_skip_empty_title",
                    extra={"theatre": theatre.slug, "raw_title": raw.movie_title},
                )
                continue

            if raw.start_time.tzinfo is None:
                logger.warning(
                    "ingest_skip_naive_datetime",
                    extra={"theatre": theatre.slug, "title": normalized},
                )
                continue

            movie = await self.movie_repo.get_or_create(title=raw.movie_title, slug=normalized)

            key = hashlib.sha256(
                f"{theatre.slug}{normalized}{raw.start_time.isoformat()}".encode()
            ).hexdigest()
            current_keys.add(key)

            try:
                inserted = await self.screening_repo.upsert(
                    theatre_id=theatre.id,
                    movie_id=movie.id,
                    start_time=raw.start_time,
                    end_time=raw.end_time,
                    idempotency_key=key,
                    raw_source_ref=raw.raw_source_ref,
                    raw_data=raw.raw_data,
                )
                count += inserted
            except Exception:
                logger.exception(
                    "ingest_screening_failed",
                    extra={"theatre": theatre.slug, "title": normalized},
                )
                continue

            if raw.attributes:
                try:
                    screening = await self.screening_repo.get_by_idempotency_key(key)
                    if screening is None:
                        logger.warning(
                            "ingest_attribute_sync_no_screening",
                            extra={"theatre": theatre.slug, "title": normalized, "key": key},
                        )
                    else:
                        attrs = await asyncio.gather(*[
                            self.attribute_repo.get_or_create(a.category, a.slug, a.label)
                            for a in raw.attributes
                        ])
                        await self.screening_repo.sync_attributes(
                            screening.id, [a.id for a in attrs]
                        )
                except Exception:
                    logger.exception(
                        "ingest_attribute_sync_failed",
                        extra={"theatre": theatre.slug, "title": normalized},
                    )

        # Remove screenings within the scrape window that are no longer advertised.
        # We bound the delete to the same horizon we scraped so that screenings beyond
        # the window (scraped in a previous run with a wider horizon) are not touched.
        # Guard: skip deletion when current_keys is empty — passing an empty exclusion
        # set to delete_stale_future would wipe all upcoming screenings for the theatre.
        # We distinguish two empty cases so each shows up distinctly in logs:
        #   - scraper returned 0 raw screenings → likely empty calendar, safe to skip
        #   - scraper returned N but all were filtered (naive datetimes / empty titles)
        #     → indicates a scraper regression; still skip deletion to avoid data loss
        now = datetime.now(timezone.utc)
        scrape_cutoff = now + timedelta(days=LOOKAHEAD_DAYS - 1)
        stale = 0
        if not current_keys:
            if not result.screenings:
                logger.warning(
                    "ingest_stale_skipped_empty_scrape",
                    extra={"theatre": theatre.slug},
                )
            else:
                logger.warning(
                    "ingest_stale_skipped_all_filtered",
                    extra={"theatre": theatre.slug, "raw_count": len(result.screenings)},
                )
        else:
            stale = await self.screening_repo.delete_stale_future(theatre.id, current_keys, now, scrape_cutoff)
            if stale:
                logger.info("ingest_stale_removed", extra={"theatre": theatre.slug, "count": stale})

        await self.scraper_run_repo.complete(
            scraper_run_id=scraper_run.id,
            ended_at=result.ended_at,
            status=ScraperRunStatus.success,
            screenings_scraped=len(result.screenings),
            screenings_inserted=count,
        )
        await self.session.commit()
        logger.info(
            "ingest_complete",
            extra={"theatre": theatre.slug, "new": count, "stale_removed": stale},
        )


async def ingest_all(results: list[ScraperResult], session: AsyncSession) -> None:
    service = IngestionService(session)
    for result in results:
        try:
            await service.ingest(result)
        except Exception:
            logger.exception("ingest_unhandled_error", extra={"theatre": result.theatre_slug})
            await session.rollback()
