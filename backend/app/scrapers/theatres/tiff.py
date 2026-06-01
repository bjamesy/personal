import re
import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, RawScreening, ScraperStrategy, TheatreConfig, detect_format_attributes

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="tiff",
    name="TIFF Bell Lightbox",
    source_url="https://www.tiff.net/calendar",
    latitude=43.6469,
    longitude=-79.3904,
)

_SKIP_TITLES = (
    "Film Reference Library",
    "Setting the Scene Exhibition",
)

_TIME_RE = re.compile(r"(\d{1,2}):(\d{2})(am|pm)", re.IGNORECASE)
_ID_RE = re.compile(r"^calendar-item-(\d{2})-(\d{2})-(\d{2})$")

# Injected before page scripts run to mask headless-browser signals.
_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-CA', 'en'] });
window.chrome = { runtime: {} };
"""


class TIFFScraper(BaseScraper):
    strategy = ScraperStrategy.js_rendered

    async def scrape(self) -> list[RawScreening]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                args=["--disable-blink-features=AutomationControlled"]
            )
            try:
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                    locale="en-CA",
                )
                await context.add_init_script(_STEALTH_SCRIPT)
                page = await context.new_page()
                await page.goto(self.config.source_url, wait_until="networkidle")
                html = await page.content()
            finally:
                await browser.close()
        return self.parse(html)

    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        for day_div in soup.find_all("div", id=_ID_RE):
            day_date = _parse_date(day_div["id"])
            if day_date is None:
                continue

            for li in day_div.find_all(
                "li", attrs={"aria-label": re.compile(r"^Screenings for ")}
            ):
                title_el = li.find("h3")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title or any(s in title for s in _SKIP_TITLES):
                    continue

                event_link = li.find("a", class_=re.compile(r"cardLink"))
                event_url = event_link["href"] if event_link else None

                schedule = li.find("div", class_=re.compile(r"cardScheduleItems"))
                if not schedule:
                    continue

                for a in schedule.find_all(
                    "a", class_=re.compile(r"screeningButtonLink|updatedButtonLink")
                ):
                    time_text = _extract_time(a)
                    if not time_text:
                        continue
                    try:
                        start_time = _parse_start(day_date, time_text)
                    except ValueError:
                        logger.warning(
                            "tiff_bad_time", extra={"time": time_text, "title": title}
                        )
                        continue
                    screenings.append(
                        RawScreening(
                            movie_title=title,
                            start_time=start_time,
                            raw_source_ref=event_url,
                            attributes=detect_format_attributes(title),
                        )
                    )

        if not screenings:
            logger.warning("tiff_no_screenings_found")
        return screenings


def _parse_date(id_str: str) -> date | None:
    m = _ID_RE.match(id_str)
    if not m:
        return None
    mm, dd, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return date(2000 + yy, mm, dd)


def _extract_time(anchor) -> str | None:
    btn = anchor.find("div")
    if not btn:
        return None
    for span in btn.find_all("span"):
        cls = " ".join(span.get("class") or [])
        if "openInNew" in cls or "material" in cls.lower():
            continue
        text = span.get_text(strip=True)
        if _TIME_RE.search(text):
            return text
    return None


def _parse_start(d: date, time_str: str) -> datetime:
    m = _TIME_RE.search(time_str)
    if not m:
        raise ValueError(f"Cannot parse time: {time_str!r}")
    hour, minute, meridiem = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=TORONTO_TZ)
