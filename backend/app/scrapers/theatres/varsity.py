import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

from app.scrapers.base import BaseScraper, RawScreening, ScraperStrategy, TheatreConfig

logger = logging.getLogger(__name__)

TORONTO_TZ = ZoneInfo("America/Toronto")

_LOOKAHEAD_DAYS = 7
_LOCATION_ID = 7199
_API_URL = "https://apis.cineplex.com/prod/cpx/theatrical/api/v1/showtimes"
_FILM_BASE_URL = "https://www.cineplex.com/en/movie"

# Public key embedded in Cineplex's JS bundle — same for all visitors.
_HEADERS = {
    "ocp-apim-subscription-key": "dcdac5601d864addbc2675a2e96cb1f8",
    "referer": "https://www.cineplex.com/",
    "accept-language": "en",
}

CONFIG = TheatreConfig(
    slug="varsity",
    name="Cineplex Cinemas Varsity and VIP",
    source_url=f"https://www.cineplex.com/theatre/cineplex-cinemas-varsity-and-vip",
)


class VarsityScraper(BaseScraper):
    strategy = ScraperStrategy.static

    async def scrape(self) -> list[RawScreening]:
        today = datetime.now(TORONTO_TZ).date()
        screenings: list[RawScreening] = []

        async with httpx.AsyncClient(headers=_HEADERS, timeout=15.0) as client:
            for i in range(_LOOKAHEAD_DAYS):
                d = today + timedelta(days=i)
                date_str = f"{d.month}/{d.day}/{d.year}"
                try:
                    r = await client.get(
                        _API_URL,
                        params={"language": "en", "locationId": _LOCATION_ID, "date": date_str},
                    )
                    r.raise_for_status()
                    if r.content:
                        screenings.extend(_parse_response(r.json()))
                except Exception:
                    logger.exception("varsity_fetch_error", extra={"date": d.isoformat()})

        return screenings


def _parse_response(data: list) -> list[RawScreening]:
    screenings: list[RawScreening] = []
    for theatre in data:
        for date_block in theatre.get("dates", []):
            for movie in date_block.get("movies", []):
                title = movie.get("name", "").strip()
                film_url = movie.get("filmUrl")
                movie_url = f"{_FILM_BASE_URL}/{film_url}" if film_url else None

                for experience in movie.get("experiences", []):
                    for session in experience.get("sessions", []):
                        if session.get("isInThePast") or not session.get("isShowtimeEnabledOnline"):
                            continue
                        start_str = session.get("showStartDateTime")
                        if not start_str or not title:
                            continue
                        try:
                            start_time = datetime.fromisoformat(start_str).replace(tzinfo=TORONTO_TZ)
                            screenings.append(RawScreening(
                                movie_title=title,
                                start_time=start_time,
                                raw_source_ref=movie_url,
                            ))
                        except ValueError:
                            logger.warning("varsity_bad_datetime", extra={"start": start_str})
    return screenings
