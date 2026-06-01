# Backlog

## Varsity scraper — Cloudflare Workers proxy
Cineplex API returns 403 from the prod server IP (Azure API Management IP block). Works fine locally. Fix: proxy requests through a Cloudflare Worker (~10 lines) so prod never hits the Cineplex endpoint directly. Worker forwards the request with the existing headers and returns JSON. Free tier (100k req/day) is more than sufficient. Varsity is currently disabled (`is_cron_enabled = false`) until this is in place.

## Scraper guardrails
Add validation to catch scraper regressions before or after ingestion. Approach: statistical baselines (rolling avg/stddev of `screenings_scraped` per theatre from historical runs) combined with lightweight heuristics (min count, date range sanity). Needs a few weeks of prod data before baselines are meaningful. Decision pending: alerting-only vs blocking ingestion on failure.
