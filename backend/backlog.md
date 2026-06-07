# Ingestion Service — Review Backlog

Findings from code review of `backend/app/ingestion/service.py` not addressed in the immediate fix.

---

## `_sync_scraper_health` runs on a broken session after partial ingest failure

**File:** `backend/app/scheduler.py:40`

After the `ingest_all` try/except, `_sync_scraper_health` always runs on the same session.
If an earlier ingest exception left the session in a bad state and the rollback itself
raised, `_sync_scraper_health`'s queries may fail or operate on stale identity-map data —
potentially triggering incorrect auto-enable/disable decisions.

**Fix direction:** Rollback before `_sync_scraper_health`, or give it a fresh session.

---

## All-filtered scrapes recorded as `success`, bypassing auto-disable circuit

**File:** `backend/app/ingestion/service.py:140`

When all scraped screenings are filtered out (e.g. scraper starts returning naive datetimes),
the run is recorded as `ScraperRunStatus.success` with `screenings_inserted=0`. The `ingest_stale_skipped_all_filtered` log now surfaces this, but `_sync_scraper_health` still
sees a clean success streak and never auto-disables the theatre.

**Fix direction:** Introduce a `ScraperRunStatus.partial` (or `empty`) status, or treat
all-filtered as a failure for the purposes of the consecutive-failure counter.

---

## `screenings_scraped` overstates the count

**File:** `backend/app/ingestion/service.py:144`

`screenings_scraped=len(result.screenings)` counts raw rows from the scraper, including
those skipped for empty titles or naive datetimes. The column therefore means "raw input
count", not "screenings attempted", creating a misleading ratio against `screenings_inserted`
in monitoring dashboards.

**Fix direction:** Change to `len(current_keys)` (valid after filtering) or add a separate
`screenings_attempted` field.

---

## `asyncio.gather` for attribute upserts runs concurrent coroutines on the same session

**File:** `backend/app/ingestion/service.py:108`

`asyncio.gather(*[self.attribute_repo.get_or_create(...) for a in raw.attributes])` fires
multiple concurrent DB operations on the same `AsyncSession`. SQLAlchemy's async session
is not safe for concurrent access. If two screenings share an attribute slug, the second
flush can hit a unique-constraint violation mid-gather, leaving the session dirty.

**Fix direction:** Replace `gather` with a sequential loop, or batch-fetch then upsert
outside the per-screening loop.

---

## `current_keys.add(key)` before the upsert try-block protects a key that may never be written

**File:** `backend/app/ingestion/service.py:79`

The idempotency key is added to `current_keys` before the `screening_repo.upsert()` call.
If the upsert raises and `continue` is taken, the key is still in the exclusion set passed
to `delete_stale_future`, so a stale DB record whose upsert consistently fails is never
cleaned up.

**Fix direction:** Move `current_keys.add(key)` inside the try-block, after a successful
upsert, or track failed keys separately.

---

## Double `get_by_slug` lookup per theatre per pipeline run

**File:** `backend/app/scheduler.py:50`

`ingest()` and `_sync_scraper_health` each call `theatre_repo.get_by_slug()` independently
for the same slugs. A single bulk fetch at the start of `run_pipeline` and a dict lookup
would halve the DB round-trips (currently 2× the number of theatres per run).
