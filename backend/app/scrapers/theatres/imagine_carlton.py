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
    slug="imagine_carlton",
    name="Imagine Cinemas Carlton",
    source_url="https://imaginecinemas.com/cinema/carlton/",
)

_SCHDATE_RE = re.compile(r"schdate=(\d{4}-\d{2}-\d{2})")


class ImagineCarItonScraper(StaticScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        for movie_div in soup.select("div.movie-showtime"):
            try:
                title_tag = movie_div.select_one("h2.movie-title")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)

                for perf in movie_div.select("a.movie-performance"):
                    href = perf.get("href", "")
                    time_text = perf.get_text(strip=True)

                    date_match = _SCHDATE_RE.search(href)
                    if not date_match:
                        continue

                    try:
                        start_time = _parse_datetime(date_match.group(1), time_text)
                    except ValueError:
                        continue

                    screenings.append(RawScreening(
                        movie_title=title,
                        start_time=start_time,
                        raw_source_ref=href,
                    ))
            except Exception:
                logger.exception("imagine_parse_error", extra={"div": str(movie_div)[:100]})

        return screenings


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    # date_str: "2026-05-29", time_str: "12:35PM"
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M%p")
    return dt.replace(tzinfo=TORONTO_TZ)
