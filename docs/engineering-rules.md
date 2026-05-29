# Engineering Rules

These rules define how all code in this repository should be written and structured.

They exist to ensure consistency, debuggability, and long-term maintainability in an AI-assisted development workflow.

---

## 1. Architecture Discipline

- This is a modular monolith.
- Do not introduce microservices.
- Do not introduce distributed systems patterns (Kafka, event buses, etc.).
- Keep all core logic inside a single backend codebase.

---

## 2. Layering Rules

The backend must follow strict separation of concerns:

### API Layer (FastAPI routes)
- Request validation only
- Calls service layer
- No business logic

### Service Layer
- Business logic lives here
- Orchestrates workflows
- Calls repositories and external services

### Repository Layer
- Database access only
- No business logic
- No orchestration

### Scraper Layer
- Only extracts raw data
- No DB access
- No normalization logic

### Ingestion Layer
- Transforms scraper output into canonical schema
- Handles idempotency logic
- Writes to DB via repositories

---

## 3. Data Integrity Rules

- All screenings must be idempotent.
- No duplicate screenings may exist in the database.
- Uniqueness is enforced via a deterministic `idempotency_key`.

### Movie Title Normalization

Movie titles must be normalized before use in idempotency keys or stored on the `Movie` record:
1. Lowercase
2. Strip all punctuation
3. Replace spaces with underscores (snake_case)

Example: `"It's a Wonderful Life!"` → `its_a_wonderful_life`

---

## 4. Idempotency Rule

- Every screening must compute a stable unique key.
- The system must safely handle repeated scraper runs without duplication.
- INSERT operations must be safe to retry.

---

## 5. Type Safety

- Use Python type hints everywhere.
- Prefer explicit types over implicit ones.
- Avoid `Any` unless absolutely necessary.

---

## 6. Async Rules

- Backend should be async-first.
- Use async DB driver (SQLAlchemy async or equivalent).
- Scrapers may be async or sync, but ingestion must be async-safe.

---

## 7. Error Handling

- Never silently swallow exceptions.
- Log all scraper failures.
- Failures in one scraper must not affect others.

---

## 8. Naming Conventions

- Use explicit names (no abbreviations like `scrp`, `mgr`, `svc`).
- Domain terms must be consistent across DB, API, and code.

Examples:
- Screening (not ShowTime, EventItem, etc.)
- Theatre (not CinemaLoc, VenueObj)

---

## 9. Code Simplicity

- Prefer simple functions over classes unless state is required.
- Avoid premature abstraction.
- Avoid over-engineering generic frameworks.

---

## 10. Scraper Rules

- Each theatre must have its own scraper module.
- Scrapers must return raw structured data only.
- Scrapers must never write to the database.
- Use `httpx` + `BeautifulSoup` for static HTML sites; use `Playwright` for JS-rendered sites.
- Playwright browser contexts must be opened and closed within the scraper run — no shared browser state between scrapers.

---

## 11. Logging

- Use structured logging (JSON-style preferred).
- Every scraper run must log:
  - start time
  - end time
  - success/failure
  - number of items extracted

---

## 12. Testing Philosophy

- Unit test ingestion logic (especially idempotency).
- Scrapers may have lightweight integration tests.
- Do not over-invest in UI testing for MVP.

---

## 13. Deployment Assumption

- System runs in Docker.
- Environment configuration is via environment variables.
- No cloud-provider-specific runtime dependencies.