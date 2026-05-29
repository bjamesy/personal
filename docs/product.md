# Product: web data aggregation system

## 1. Overview

A system that scrapes data from a small set of external small movie theatre websites (urls to be provided) in toronto for specific information relevant to screenings for a current month and normalizes the data into a consistent schema, stores historical data in our database and exposes it through a simple web ui.
The system runs on a scheduled basis several times per day and is designed for reliability, maintainability, and ease of adding new sources.

---

## 2. Problem statement

Data for daily screenings in toronto is distributed across multiple websites with inconsistent formats. Manually checking and consolidating this information is time-consuming and error-prone

This system automates:
- data collection
- normalization
- storage
- visualization

---

## 3. Goals (MVP)

- Scrape data from ~7 predefined websites
- Run scraping jobs multiple times per day (scheduled)
- Normalize scraped data into a consistent internal schema
- Persist all scraped screenings; past screenings serve as the historical record
- Provide a simple frontend to view latest and historical data
- Handle partial failures gracefully (one site failing should not break system)

---

## 4. Non-Goals (Important)

- No user accounts or authentication (initially)
- No multi-tenant support
- No distributed system / microservices architecture
- No real-time streaming updates
- No heavy analytics or ML pipelines
- No complex UI dashboards (keep it minimal)

---

## 5. Users

Single primary user (developer/operator).

Future possibility:
- small internal team or clients consuming aggregated data

---

## 6. Core Use Cases

### UC1: Scheduled Data Collection
System automatically scrapes configured sources 2–6 times per day.

### UC2: Data Normalization
Each source maps into a shared canonical schema.

### UC3: Historical Tracking
All screenings are retained in the database. Screenings with a past start_time constitute the historical record. Screenings are immutable once inserted; cancellation handling is out of scope.

### UC4: Data Viewing
Frontend displays:
- latest data per source
- past screenings

---

## 7. Data Sources

- ~7 external websites initially
- Each site may require different scraping strategies:
  - static HTML scraping
  - JS-rendered scraping (if needed)
- Sources will evolve over time

---

## 8. High-Level Requirements

- Reliable scheduled execution of scraping jobs
- Isolation between scrapers (one failure does not impact others)
- Retry strategy for transient failures
- Structured logging for debugging scraping issues
- Ability to add new scraper modules easily

---

## 9. Data Expectations

Each scraped record should support:
- source identifier
- timestamp of scrape
- raw data (optional storage for debugging)
- normalized structured representation
- unique per screening date and time, movie and theatre

Historical data must be preserved.

---

## 10. Success Criteria

MVP is successful when:

- All configured sources are scraped reliably on schedule
- Data is stored consistently in database
- Frontend can display latest + historical data
- Adding a new scraper requires minimal changes to core system
- System can run locally via simple setup (e.g. Docker Compose)

---

## 11. Constraints

- Solo developer system
- Low infrastructure cost
- Prefer simplicity over scalability
- Maintainability > performance optimization
- Accept eventual need for refactoring, but avoid premature complexity

---

## 12. Out of Scope (Explicit)

- No Kafka/event streaming systems
- No multi-service distributed architecture
- No real-time WebSockets requirement
- No AI inference pipeline (unless added later)
- No advanced observability stack initially
- No screening cancellation or update handling

---

## 13. Key Design Philosophy

- Keep architecture monolithic until proven otherwise
- Prefer scheduled batch jobs over real-time systems
- Treat each scraper as an isolated module
- Normalize data as early as practical, but preserve raw input
- Optimize for debuggability of scraping failures