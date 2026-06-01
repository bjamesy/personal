import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, RawScreening, ScraperStrategy, TheatreConfig, detect_format_attributes

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="fox",
    name="Fox Theatre",
    source_url="https://www.foxtheatre.ca/whats-on/now-showing/",
    latitude=43.6389,
    longitude=-79.4404,
)


class FoxScraper(BaseScraper):
    strategy = ScraperStrategy.js_rendered

    async def scrape(self) -> list[RawScreening]:
        # Fox uses Elementor + FullCalendar which never reaches networkidle.
        # Use load + a short extra wait for FullCalendar to render its grid.
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(self.config.source_url, wait_until="load", timeout=30000)
                await page.wait_for_timeout(3000)
                html = await page.content()
            finally:
                await browser.close()
        return self.parse(html)

    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        # FullCalendar renders each day as td[data-date="YYYY-MM-DD"] containing
        # a.fc-event elements with div.fc-event-time and div.fc-event-title children.
        for day_cell in soup.select("td[data-date]"):
            date_str = day_cell.get("data-date", "")
            if not date_str:
                continue

            for event in day_cell.select("a.fc-event"):
                try:
                    time_tag = event.select_one("div.fc-event-time")
                    title_tag = event.select_one("div.fc-event-title")
                    if not time_tag or not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    time_text = time_tag.get_text(strip=True)  # "3:15 PM"

                    try:
                        start_time = _parse_datetime(date_str, time_text)
                    except ValueError:
                        continue

                    screenings.append(RawScreening(
                        movie_title=title,
                        start_time=start_time,
                        raw_source_ref=event.get("href"),
                        attributes=detect_format_attributes(title),
                    ))
                except Exception:
                    logger.exception("fox_parse_error", extra={"date": date_str})

        return screenings


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    # date_str: "2026-05-29", time_str: "3:15 PM"
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
    return dt.replace(tzinfo=TORONTO_TZ)
