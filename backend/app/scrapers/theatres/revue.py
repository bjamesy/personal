import json
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.scrapers.base import RawScreening, TheatreConfig
from app.scrapers.static import StaticScraper

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="revue",
    name="Revue Cinema",
    source_url="https://revuecinema.ca/calendar/",
)

_YEAR_RE = re.compile(r"\(\d{4}\)")

_SKIP_SUBSTRINGS = (
    "CLOSED FOR PRIVATE RENTAL",
    "48 Hour Film",
    "FOUND FOOTAGE FEST",
)


class RevueScraper(StaticScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        events = _extract_events(soup)
        if not events:
            logger.warning("revue_no_events_found")
            return []

        screenings: list[RawScreening] = []
        for event in events:
            raw_title = event.get("title", "")
            start_str = event.get("start", "")
            url = event.get("url") or None

            film_title = _extract_film_title(raw_title)
            if film_title is None:
                continue

            try:
                start_time = _parse_start(start_str)
            except ValueError:
                logger.warning("revue_bad_datetime", extra={"start": start_str})
                continue

            screenings.append(RawScreening(
                movie_title=film_title,
                start_time=start_time,
                raw_source_ref=url,
            ))

        return screenings


def _extract_events(soup: BeautifulSoup) -> list[dict]:
    for script in soup.find_all("script"):
        text = script.string or ""
        m = re.search(r"events:\s*(\[)", text)
        if not m:
            continue
        try:
            events, _ = json.JSONDecoder().raw_decode(text, m.start(1))
            return events
        except json.JSONDecodeError:
            continue
    return []


def _extract_film_title(raw: str) -> str | None:
    raw = raw.strip()
    if not raw or any(s in raw for s in _SKIP_SUBSTRINGS):
        return None

    # Separate series name from film title on the first colon
    if ":" in raw:
        film_part = raw.split(":", 1)[1].strip()
    else:
        film_part = raw

    # Trim at year boundary "(YYYY)" — include the year in the title
    m = _YEAR_RE.search(film_part)
    if m:
        film_part = film_part[: m.end()].strip()
    else:
        # No year: trim at qualifier suffix delimited by " - ", " – ", or
        # the literal "u2013"/"u2014" that WordPress sometimes emits instead
        # of a proper JSON \u escape.
        for sep in (" - ", " – ", " — ", " u2013 ", " u2014 "):
            idx = film_part.find(sep)
            if idx != -1:
                film_part = film_part[:idx].strip()
                break

    if not film_part:
        return None

    return " ".join(word.capitalize() for word in film_part.split())


def _parse_start(start_str: str) -> datetime:
    return datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TORONTO_TZ)
