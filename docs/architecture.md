# Architecture: Toronto Film Tracker

## 1. System Overview

This system aggregates movie screening schedules from ~7 independent Toronto theatres, normalizes them into a unified schema, and stores them in a PostgreSQL database with historical tracking and strict idempotency guarantees.

Scraping runs on a scheduled batch basis multiple times per day. A simple web frontend displays the latest and historical screening data.

The system is designed as a **modular monolith** optimized for simplicity, maintainability, and reliability.

---

## 2. High-Level Architecture
            +----------------------+
            |  Scheduler (cron)    |
            +----------+-----------+
                       |
                       v
            +----------------------+
            |  Scraper Runner     |
            +----------+-----------+
                       |
     +-----------------+-----------------+
     |                 |                 |
     v                 v                 v
     +----------------+ +----------------+ +----------------+
    | Theatre Scraper| | Theatre Scraper| | Theatre Scraper|
    +----------------+ +----------------+ +----------------+
    \ | /
    \ | /
    v v v
    +----------------------+
    | Ingestion Layer |
    | (Normalize + Upsert) |
    +----------+-----------+
    |
    v
    +----------------------+
    | PostgreSQL DB |
    +----------+-----------+
    |
    v
    +----------------------+
    | FastAPI Backend |
    +----------+-----------+
    |
    v
    +----------------------+
    | Next.js Frontend |
    +----------------------+


---

## 3. Core Domain Concept

### Screening

A screening represents a single movie showing at a specific theatre and time.

It is treated as an **immutable event** once inserted.

---

## 4. Data Model (Logical)

### Theatre
- id (UUID)
- name
- slug
- source_url

---

### Movie
- id (UUID)
- title (normalized string)

---

### Screening
- id (UUID)
- theatre_id (FK)
- movie_id (FK)
- start_time (timestamp)
- end_time (nullable timestamp)
- idempotency_key (string, UNIQUE)
- raw_source_ref (string, optional)
- created_at (timestamp)

---

## 5. Idempotency Strategy (Critical)

Each screening must be uniquely identifiable across repeated scraper runs.

### Idempotency Key Definition
idempotency_key =
sha256(
theatre_slug +
normalized_movie_title +
ISO8601_start_time
)

---

### Guarantee

- If screening already exists → NO-OP
- If new → INSERT
- If scraper runs again → safe duplicate prevention via DB constraint

---

### Database Constraint

```sql
UNIQUE (idempotency_key)