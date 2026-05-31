import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.scrapers.base import RawScreening, TheatreConfig, detect_format_attributes
from app.scrapers.js_rendered import JSRenderedScraper

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

# TOPS screenings are outdoor with no fixed time — use 21:00 ET as dusk approximation
_DEFAULT_HOUR = 21

CONFIG = TheatreConfig(
    slug="tops",
    name="Toronto Outdoor Picture Show",
    source_url="https://www.topictureshow.com/2026-calendar",
)

# Matches both full names (AUGUST) and 3-letter abbreviations (AUG)
_MONTH_RE = re.compile(
    r"(JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?"
    r"|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"
    r"\s+(\d{1,2})",
    re.IGNORECASE,
)


class TOPSScraper(JSRenderedScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        # Squarespace renders each film as a sqs-html-content block containing:
        #   h3 → date + venue (e.g. "THURS JULY 2\nCORKTOWN COMMON")
        #   h2 > a → film title (relative href distinguishes films from venue summary blocks)
        for block in soup.select("div.sqs-html-content"):
            try:
                title_tag = block.select_one("h2 a, h1 a")
                date_tag = block.select_one("h3, h4")
                if not title_tag or not date_tag:
                    continue

                # Venue summary blocks link to absolute URLs; film blocks use relative paths
                href = title_tag.get("href", "")
                if not href.startswith("/") or href.startswith("//"):
                    continue

                title = title_tag.get_text(strip=True)
                date_text = date_tag.get_text(" ", strip=True).upper()

                date_match = _MONTH_RE.search(date_text)
                if not date_match:
                    continue

                try:
                    start_time = _parse_date(date_match.group(1), date_match.group(2))
                except ValueError:
                    continue

                screenings.append(RawScreening(
                    movie_title=title,
                    start_time=start_time,
                    raw_source_ref=urljoin(self.config.source_url, href),
                    attributes=detect_format_attributes(title),
                ))
            except Exception:
                logger.exception("tops_parse_error", extra={"block": str(block)[:100]})

        return screenings


def _parse_date(month_str: str, day_str: str) -> datetime:
    now = datetime.now(TORONTO_TZ)
    for year in (now.year, now.year + 1):
        for fmt in ("%B %d %Y", "%b %d %Y"):
            try:
                dt = datetime.strptime(f"{month_str} {day_str} {year}", fmt)
                result = dt.replace(hour=_DEFAULT_HOUR, tzinfo=TORONTO_TZ)
                if result.date() >= now.date():
                    return result
            except ValueError:
                continue
    raise ValueError(f"Cannot parse date: {month_str} {day_str}")
