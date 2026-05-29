# Implementation Plan: Toronto Theatre Screening Aggregator

This document defines the build order for the system to minimize rework and ensure early validation of core assumptions.

---

## Phase 1: Project Foundation

### 1. Repository Setup
- Initialize monorepo structure
- Create backend (FastAPI)
- Create frontend (Next.js)
- Add Docker Compose setup

---

### 2. Infrastructure Setup
- PostgreSQL container
- Backend container (includes Playwright + Chromium for JS-rendered scraping)
- Frontend container
- Basic environment variable system

---

## Phase 2: Core Data Model

### 3. Database Schema
Implement:
- theatres table
- movies table
- screenings table (include `raw_data jsonb`, `idempotency_key` UNIQUE constraint, `created_at`)
- scraper_runs table (include `status` enum: success | failure, `items_extracted`, `error_message`)

---

### 4. Migration System
- Set up Alembic
- Ensure reproducible schema creation

---

## Phase 3: Backend Layers

### 5. Repository Layer
- Implement async repository classes for each model
- All DB access goes through repositories — no raw queries elsewhere

---

### 6. Service Layer
- Implement service classes for screening queries
- Business logic lives here; services call repositories

---

## Phase 4: Scraping Layer

### 7. Scraper Interface Design
Define standard interface:
- input: theatre config
- output: raw screenings list

Each scraper module declares its strategy: `static` (httpx + BeautifulSoup) or `js_rendered` (Playwright). The scraper runner does not need to know the difference.

---

### 8. Implement First Scraper (Static HTML)
- Pick one static HTML theatre site
- Implement full extraction pipeline
- Validate raw data shape

---

### 9. Implement First JS-Rendered Scraper (Playwright)
- Pick one JS-rendered theatre site
- Open and close a Playwright browser context within the scraper run
- Validate Playwright integration in Docker

---

### 10. Add Remaining Scrapers
- One module per theatre
- Declare strategy per scraper
- Ensure consistent output format

---

## Phase 5: Ingestion Pipeline

### 11. Build Ingestion Layer
- Normalize movie titles: lowercase → strip punctuation → snake_case
- Compute idempotency keys: `sha256(theatre_slug + normalized_title + ISO8601_start_time)`
- Write screenings via Repository layer (ON CONFLICT DO NOTHING)
- Store `raw_data` (jsonb) on each screening record
- Record `ScraperRun` (started_at, ended_at, status, items_extracted, error_message) per theatre per run

---

### 12. End-to-End Pipeline Test
- Run scraper → ingestion → DB
- Validate deduplication works
- Validate ScraperRun records are written correctly

---

## Phase 6: Scheduling System

### 13. Add Cron-Based Scheduler
- Run full scraping pipeline 2–6 times daily
- Ensure failure isolation per scraper (one failure does not stop others)

---

## Phase 7: API Layer

### 14. Build FastAPI Endpoints
Routes (validation only — delegate to service layer):
- `GET /screenings?month=`
- `GET /screenings/latest`
- `GET /theatres`
- `GET /scraper-runs` (latest run per theatre, for observability)

---

## Phase 8: Frontend

### 15. Basic Calendar UI
- Monthly calendar view
- Filter by theatre
- Display screenings per day

---

## Phase 9: Hardening

### 16. Edge Case Handling
- Missing data
- Malformed HTML
- Timezone inconsistencies
- Migrations where necessary
- Concurrency on scrapers

---

## Guiding Principle

Always validate the full pipeline early:

    Scraper → Ingestion → DB → API → UI

before expanding complexity.
