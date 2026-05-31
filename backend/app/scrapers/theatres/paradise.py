import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.scrapers.base import RawScreening, TheatreConfig, detect_format_attributes
from app.scrapers.static import StaticScraper

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="paradise",
    name="Paradise Theatre",
    source_url="https://paradiseonbloor.com/coming-soon/",
)


class ParadiseScraper(StaticScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        for show in soup.select("div.show-details"):
            try:
                title_tag = show.select_one("h2.show-title a.title")
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)

                for date_li in show.select("ul.datelist li.show-date"):
                    data_date = date_li.get("data-date", "")
                    date_text = " ".join(date_li.get_text(strip=True).split())

                    for showtime_li in show.select(f"ol.showtimes li[data-date='{data_date}']"):
                        time_tag = showtime_li.select_one("a.showtime")
                        if not time_tag:
                            continue
                        time_text = time_tag.get_text(strip=True)

                        if not re.search(r"\d:\d{2}", time_text):
                            continue

                        try:
                            start_time = _parse_datetime(date_text, time_text)
                        except ValueError:
                            continue

                        purchase_link = showtime_li.select_one("a.showtime")
                        screenings.append(RawScreening(
                            movie_title=title,
                            start_time=start_time,
                            raw_source_ref=purchase_link.get("href") if purchase_link else None,
                            attributes=detect_format_attributes(title),
                        ))
            except Exception:
                logger.exception("paradise_parse_error", extra={"show": str(show)[:100]})

        return screenings


def _parse_datetime(date_text: str, time_text: str) -> datetime:
    # date_text: "Sat, May 30" — strip day-of-week prefix
    if "," in date_text:
        date_text = date_text.split(",", 1)[1].strip()

    now = datetime.now(TORONTO_TZ)
    time_text = time_text.upper().replace(".", "")  # "3:45 PM"

    for year in (now.year, now.year + 1):
        for fmt in ("%B %d %Y %I:%M %p", "%b %d %Y %I:%M %p"):
            try:
                dt = datetime.strptime(f"{date_text} {year} {time_text}", fmt)
                result = dt.replace(tzinfo=TORONTO_TZ)
                if result >= now - timedelta(days=7):
                    return result
            except ValueError:
                continue

    raise ValueError(f"Cannot parse: {date_text!r} {time_text!r}")
