import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.scrapers.base import RawScreening, TheatreConfig, detect_format_attributes
from app.scrapers.js_rendered import JSRenderedScraper

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="hotdocs",
    name="Hot Docs Cinema",
    source_url=(
        "https://boxoffice.hotdocs.ca/websales/pages/list.aspx"
        "?cp242=KenticoInclude&epguid=a2104450-7e47-4369-a17d-c247570c3939&"
    ),
    latitude=43.6655,
    longitude=-79.4086,
)


class HotDocsScraper(JSRenderedScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        # Each span.Showing carries data-agl_name (title) and data-agl_date (datetime)
        for showing in soup.select("span.Showing[data-agl_date]"):
            try:
                title = showing.get("data-agl_name", "").strip()
                date_str = showing.get("data-agl_date", "").strip()

                if not title or not date_str:
                    continue

                try:
                    start_time = _parse_datetime(date_str)
                except ValueError:
                    continue

                # Ticketing links are javascript:void(0) — not useful as a ref
                screenings.append(RawScreening(
                    movie_title=title,
                    start_time=start_time,
                    raw_data={"agl_date": date_str},
                    attributes=detect_format_attributes(title),
                ))
            except Exception:
                logger.exception("hotdocs_parse_error", extra={"showing": str(showing)[:100]})

        return screenings


def _parse_datetime(date_str: str) -> datetime:
    # Format: "5/29/26 07:00 P" where P=PM, A=AM
    date_str = date_str.strip()
    if date_str.endswith(" P"):
        date_str = date_str[:-2] + " PM"
    elif date_str.endswith(" A"):
        date_str = date_str[:-2] + " AM"
    dt = datetime.strptime(date_str, "%m/%d/%y %I:%M %p")
    return dt.replace(tzinfo=TORONTO_TZ)
