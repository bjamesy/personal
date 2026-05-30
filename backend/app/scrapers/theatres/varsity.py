import re
import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, RawScreening, ScraperStrategy, TheatreConfig

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

_LOOKAHEAD_DAYS = 7
_BASE_URL = "https://www.cineplex.com/theatre/cineplex-cinemas-varsity-and-vip"
_DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August"
    r"|September|October|November|December)\s+(\d+),?\s+(\d{4})"
)

CONFIG = TheatreConfig(
    slug="varsity",
    name="Cineplex Cinemas Varsity and VIP",
    source_url=_BASE_URL,
)


class VarsityScraper(BaseScraper):
    strategy = ScraperStrategy.js_rendered

    async def scrape(self) -> list[RawScreening]:
        today = datetime.now(TORONTO_TZ).date()
        dates = [today + timedelta(days=i) for i in range(_LOOKAHEAD_DAYS)]
        screenings: list[RawScreening] = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                for d in dates:
                    url = f"{_BASE_URL}?openTM=true&date={d.isoformat()}"
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        html = await page.content()
                        screenings.extend(self.parse(html))
                    except Exception:
                        logger.exception("varsity_fetch_error", extra={"date": d.isoformat()})
            finally:
                await browser.close()

        return screenings

    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")

        page_date = _extract_date(soup)
        if page_date is None:
            logger.warning("varsity_no_date_found")
            return []

        screenings: list[RawScreening] = []

        for container in soup.find_all("div", class_=re.compile(r"MovieDetails_showtimesContainer")):
            h3 = container.find("h3", class_=re.compile(r"cpx-hidden-md-down"))
            title = h3.get_text(strip=True) if h3 else None
            if not title:
                continue

            link = container.find("a", class_=re.compile(r"MoviePosterImage_linkContainer"))
            movie_url = link["href"] if link else None

            for btn in container.find_all(
                "button", attrs={"aria-label": re.compile(r"^Book show at ")}
            ):
                time_str = btn["aria-label"].removeprefix("Book show at ").strip()
                try:
                    start_time = _parse_start(page_date, time_str)
                except ValueError:
                    logger.warning(
                        "varsity_bad_time", extra={"time": time_str, "title": title}
                    )
                    continue
                screenings.append(
                    RawScreening(
                        movie_title=title,
                        start_time=start_time,
                        raw_source_ref=movie_url,
                    )
                )

        if not screenings:
            logger.warning("varsity_no_screenings_found", extra={"date": str(page_date)})
        return screenings


def _extract_date(soup: BeautifulSoup) -> date | None:
    date_btn = soup.find(attrs={"data-testid": "select-date"})
    if not date_btn:
        return None
    selected = date_btn.find(class_=re.compile(r"selectedOption"))
    if not selected:
        return None
    m = _DATE_RE.search(selected.get_text())
    if not m:
        return None
    try:
        return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y").date()
    except ValueError:
        return None


def _parse_start(d: date, time_str: str) -> datetime:
    # time_str is like "5:20 PM" or "10:30 PM"
    t = datetime.strptime(time_str, "%I:%M %p")
    return datetime(d.year, d.month, d.day, t.hour, t.minute, tzinfo=TORONTO_TZ)
