import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.scrapers.base import RawScreening, TheatreConfig
from app.scrapers.static import StaticScraper

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="revue",
    name="Revue Cinema",
    source_url="https://revuecinema.ca/films/",
)


class RevueScraper(StaticScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        for card in soup.select("div.movie-card"):
            try:
                title_tag = card.select_one("h5 a") or card.select_one("h4 a")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                link = title_tag.get("href")

                for date_div in card.select("div.brxe-ndxpjc"):
                    date_text = date_div.get_text(strip=True)
                    if not date_text:
                        continue
                    try:
                        start_time = _parse_datetime(date_text)
                    except ValueError:
                        continue
                    screenings.append(RawScreening(
                        movie_title=title,
                        start_time=start_time,
                        raw_source_ref=link,
                    ))
            except Exception:
                logger.exception("revue_parse_error", extra={"card": str(card)[:100]})

        return screenings


def _parse_datetime(text: str) -> datetime:
    # "Fri May 29, 09:30 PM"
    text = text.replace(",", "").strip()
    now = datetime.now(TORONTO_TZ)
    for year in (now.year, now.year + 1):
        try:
            dt = datetime.strptime(f"{text} {year}", "%a %b %d %I:%M %p %Y")
            result = dt.replace(tzinfo=TORONTO_TZ)
            if result >= now - timedelta(days=1):
                return result
        except ValueError:
            continue
    raise ValueError(f"Cannot parse Revue date: {text!r}")
