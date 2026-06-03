import html as html_lib
import json
import logging
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright

from app.scrapers.base import LOOKAHEAD_DAYS, BaseScraper, RawScreening, ScraperStrategy, TheatreConfig, detect_format_attributes

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")
_BASE_URL = "https://omniwebticketing6.com/imaginecinemas/carlton/"
_GMOVIEDATA_RE = re.compile(r"var gMovieData = (\{)")

CONFIG = TheatreConfig(
    slug="imagine_carlton",
    name="Imagine Cinemas Carlton",
    source_url=_BASE_URL,
    latitude=43.6619,
    longitude=-79.3793,
)


class ImagineCarItonScraper(BaseScraper):
    strategy = ScraperStrategy.js_rendered

    async def scrape(self) -> list[RawScreening]:
        today = datetime.now(TORONTO_TZ).date()
        dates = [today + timedelta(days=i) for i in range(LOOKAHEAD_DAYS)]
        screenings: list[RawScreening] = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                for date in dates:
                    date_str = date.strftime("%Y-%m-%d")
                    url = f"{_BASE_URL}?schdate={date_str}"
                    try:
                        await page.goto(url, wait_until="load", timeout=30000)
                        html = await page.content()
                        screenings.extend(self.parse(html))
                    except Exception:
                        logger.exception("imagine_carlton_fetch_error", extra={"date": date_str})
            finally:
                await browser.close()

        return screenings

    def parse(self, html: str) -> list[RawScreening]:
        m = _GMOVIEDATA_RE.search(html)
        if not m:
            return []

        # Brace-match to extract the full JSON object
        start = m.start(1)
        depth = 0
        end = start
        for i in range(start, len(html)):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        try:
            data = json.loads(html[start:end])
        except json.JSONDecodeError:
            logger.exception("imagine_carlton_json_error")
            return []

        screenings: list[RawScreening] = []

        for film in data.values():
            title = html_lib.unescape(film.get("title", "")).strip()
            if not title:
                continue

            for aud in film.get("schAuds", {}).values():
                for perf_type in ("schPerfsGeneral", "schPerfsReserved"):
                    perfs = aud.get(perf_type, {})
                    if not isinstance(perfs, dict):
                        continue
                    for perf in perfs.values():
                        try:
                            curtain = perf["curtainTime"]  # "2026-05-30 21:30"
                            link_str = perf.get("linkStr", "")
                            start_time = _parse_datetime(curtain)
                            raw_source_ref = _BASE_URL + link_str if link_str else None
                            screenings.append(RawScreening(
                                movie_title=title,
                                start_time=start_time,
                                raw_source_ref=raw_source_ref,
                                attributes=detect_format_attributes(title),
                            ))
                        except (KeyError, ValueError):
                            continue

        return screenings


def _parse_datetime(curtain_time: str) -> datetime:
    # Format: "2026-05-30 21:30"
    dt = datetime.strptime(curtain_time, "%Y-%m-%d %H:%M")
    return dt.replace(tzinfo=TORONTO_TZ)
