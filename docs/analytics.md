# Analytics: Visitor Visibility

## 1. Overview

There is no third-party analytics (no Google Analytics, no ad network trackers). Visitor
visibility comes from Caddy's own access logs, summarized into a dashboard by GoAccess.
This was added to get real traffic numbers before making any decisions that depend on
traffic volume (e.g. whether monetization is worth pursuing).

---

## 2. How it works

```
Caddy (access logs, JSON) --> shared volume --> goaccess container
                                                      |
                                                      | every 5 min:
                                                      | 1. jq: JSON log -> Combined Log Format
                                                      | 2. goaccess: CLF -> static HTML report
                                                      v
                                            shared volume (report.html)
                                                      |
                                                      v
                              Caddy serves it at stats.whats-screening-to.ca (basic auth)
```

- `whats-screening-to.ca` and `api.whats-screening-to.ca` both write JSON access logs to
  `/var/log/caddy/access.log` (Docker volume `caddy_logs`).
- The `goaccess` service (docker-compose.prod.yml) tails that file, converts each line to
  Combined Log Format via `jq`, and runs GoAccess to regenerate a static HTML report every
  5 minutes into the `goaccess_report` volume.
- Caddy serves that report at `stats.whats-screening-to.ca`, protected by HTTP basic auth.

## 3. Why JSON -> CLF conversion instead of GoAccess's native Caddy support

GoAccess ships a predefined `--log-format=CADDY`, but as of GoAccess 1.10.2 it does not
correctly parse Caddy's actual JSON output (fails with "No time format was found on your
conf file" — see [goaccess#2380](https://github.com/allinurl/goaccess/issues/2380)).
Separately, Caddy's JSON logs serialize the request headers as a Go map, whose key order
is not stable between requests — so any parser that depends on positional/ordered fields
(rather than parsing real JSON) is unreliable.

Converting each line to Combined Log Format with `jq` (which reads fields by name,
regardless of order) sidesteps both problems and lets GoAccess use its long-established,
well-tested `COMBINED` parser instead of the newer JSON-specific one.

## 4. Accessing the dashboard

- URL: `https://stats.whats-screening-to.ca`
- Username: `admin`
- Password: set at setup time — not stored in this repo. If lost, rotate it (see below).

### Rotating the password

```bash
# generate a new password + bcrypt hash
docker run --rm caddy:2-alpine caddy hash-password --plaintext '<new-password>'
```

Replace the hash in the `basic_auth` block for `stats.whats-screening-to.ca` in the
`Caddyfile`, then redeploy.

## 5. Operational notes

- Report data lags up to 5 minutes behind real traffic (regeneration interval).
- "Unique visitors" is IP + date + user-agent based, per GoAccess's definition — not a
  precise unique-human count, but good enough for order-of-magnitude traffic decisions.
- Requires a DNS A record for `stats.whats-screening-to.ca` pointing at the server;
  Caddy provisions its TLS certificate automatically like the other subdomains.
- No data leaves the server — everything is self-hosted, no third-party script or
  tracking pixel on the site itself.
