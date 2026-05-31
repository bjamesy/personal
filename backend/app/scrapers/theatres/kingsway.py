import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from app.scrapers.base import RawScreening, TheatreConfig, detect_format_attributes
from app.scrapers.static import StaticScraper

TORONTO_TZ = ZoneInfo("America/Toronto")

CONFIG = TheatreConfig(
    slug="kingsway",
    name="Kingsway Movies",
    source_url="http://kingswaymovies.ca/index.html",
)

# Lookahead window: generate screenings for today + next N days
_LOOKAHEAD_DAYS = 14

_DAY_NUM = {
    "mon": 0, "monday": 0,
    "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}

_DAY_WORD = r"(?:Mon(?:day)?|Tue(?:s(?:day)?)?|Wed(?:nesday)?|Thu(?:rs(?:day)?)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)"
_RANGE_RE = re.compile(rf"({_DAY_WORD})\s+to\s+({_DAY_WORD})", re.IGNORECASE)
_DAY_RE = re.compile(rf"\b({_DAY_WORD})\b", re.IGNORECASE)
_TIME_RE = re.compile(r"\d{1,2}:\d{2}\s*(?:am|pm)", re.IGNORECASE)
_SCHEDULE_START_RE = re.compile(rf"\b(?:daily|{_DAY_WORD})\b", re.IGNORECASE)


class KingswayScraper(StaticScraper):
    def parse(self, html: str) -> list[RawScreening]:
        soup = BeautifulSoup(html, "html.parser")
        screenings: list[RawScreening] = []

        for img in soup.find_all("img", alt=True):
            alt = img["alt"].strip()
            if not alt or not _SCHEDULE_START_RE.search(alt):
                continue

            title, groups = _split_title_and_groups(alt)
            if not title:
                continue

            for days, times in groups:
                if not days or not times:
                    continue
                for show_date in _upcoming_dates(days):
                    for time_str in times:
                        try:
                            start_time = _build_datetime(show_date, time_str)
                        except ValueError:
                            continue
                        screenings.append(RawScreening(
                            movie_title=title,
                            start_time=start_time,
                            raw_data={"alt": alt},
                            attributes=detect_format_attributes(alt),
                        ))

        return screenings


def _split_title_and_groups(alt: str) -> tuple[str, list[tuple[set[int], list[str]]]]:
    """Split alt text into (title, [(days, times), ...])."""
    segments = [s.strip() for s in alt.split("/")]

    # Title is everything in the first segment before the first day/daily word
    m = _SCHEDULE_START_RE.search(segments[0])
    title = segments[0][:m.start()].strip() if m else segments[0].strip()
    first_schedule = segments[0][m.start():].strip() if m else ""

    all_segments = ([first_schedule] if first_schedule else []) + segments[1:]
    groups = [_parse_group(seg) for seg in all_segments if seg]
    return title, groups


def _parse_group(text: str) -> tuple[set[int], list[str]]:
    times = [t.strip() for t in _TIME_RE.findall(text)]

    days: set[int] = set()
    if re.search(r"\bdaily\b", text, re.IGNORECASE):
        days = set(range(7))
        return days, times

    # Consume range patterns first, then individual days
    remaining = text
    for m in _RANGE_RE.finditer(text):
        start = _lookup_day(m.group(1))
        end = _lookup_day(m.group(2))
        if start <= end:
            days.update(range(start, end + 1))
        else:
            days.update(range(start, 7))
            days.update(range(0, end + 1))
        remaining = remaining[:m.start()] + " " + remaining[m.end():]

    for m in _DAY_RE.finditer(remaining):
        days.add(_lookup_day(m.group(1)))

    return days, times


def _lookup_day(name: str) -> int:
    key = name.lower()
    # Try progressively shorter prefixes to match abbreviations
    for length in (len(key), 5, 4, 3):
        candidate = key[:length]
        if candidate in _DAY_NUM:
            return _DAY_NUM[candidate]
    return _DAY_NUM[key[:3]]


def _upcoming_dates(days: set[int]) -> list[date]:
    today = datetime.now(TORONTO_TZ).date()
    return [
        today + timedelta(days=i)
        for i in range(_LOOKAHEAD_DAYS)
        if (today + timedelta(days=i)).weekday() in days
    ]


def _build_datetime(show_date: date, time_str: str) -> datetime:
    # Normalise: insert a space before am/pm if absent, then uppercase.
    normalised = re.sub(r"([ap])m$", r" \1m", time_str.strip(), flags=re.IGNORECASE).upper()
    dt = datetime.strptime(f"{show_date} {normalised}", "%Y-%m-%d %I:%M %p")
    return dt.replace(tzinfo=TORONTO_TZ)
