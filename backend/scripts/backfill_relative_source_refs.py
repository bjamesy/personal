"""
One-off script: resolve relative raw_source_ref values to absolute URLs.

Finds all screenings where raw_source_ref starts with '/' and prepends the
base URL (scheme + host) derived from the theatre's source_url.

Usage:
    DATABASE_URL=postgresql+asyncpg://... python -m scripts.backfill_relative_source_refs
"""

import asyncio
import os
from urllib.parse import urljoin

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models.screening import Screening
from app.models.theatre import Theatre


async def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        rows = await session.execute(
            select(Screening.id, Screening.raw_source_ref, Theatre.source_url)
            .join(Theatre, Screening.theatre_id == Theatre.id)
            .where(Screening.raw_source_ref.like("/%"))
        )
        results = rows.all()

        if not results:
            print("No relative raw_source_ref values found.")
            return

        print(f"Found {len(results)} rows to update.")
        for screening_id, raw_source_ref, source_url in results:
            absolute = urljoin(source_url, raw_source_ref)
            await session.execute(
                update(Screening)
                .where(Screening.id == screening_id)
                .values(raw_source_ref=absolute)
            )
            print(f"  {raw_source_ref!r}  →  {absolute!r}")

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
