import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class ScraperStrategy(enum.Enum):
    static = "static"
    js_rendered = "js_rendered"


@dataclass
class TheatreConfig:
    slug: str
    name: str
    source_url: str
    latitude: float | None = None
    longitude: float | None = None


@dataclass
class RawAttribute:
    category: str
    slug: str
    label: str


_FORMAT_CHECKS = [
    ("70mm", "70mm", "70mm Film"),
    ("35mm", "35mm", "35mm Film"),
]


def detect_format_attributes(text: str) -> list[RawAttribute]:
    lower = text.lower()
    return [
        RawAttribute(category="format", slug=slug, label=label)
        for pattern, slug, label in _FORMAT_CHECKS
        if pattern in lower
    ]


@dataclass
class RawScreening:
    movie_title: str
    start_time: datetime
    end_time: datetime | None = None
    raw_source_ref: str | None = None
    raw_data: dict | None = None
    attributes: list[RawAttribute] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.movie_title or not self.movie_title.strip():
            raise ValueError("movie_title cannot be empty")
        if self.start_time.tzinfo is None:
            raise ValueError("start_time must be timezone-aware")


@dataclass
class ScraperResult:
    theatre_slug: str
    started_at: datetime
    ended_at: datetime
    success: bool
    screenings: list[RawScreening] = field(default_factory=list)
    error: str | None = None


class BaseScraper(ABC):
    strategy: ScraperStrategy

    def __init__(self, config: TheatreConfig) -> None:
        self.config = config

    @abstractmethod
    async def scrape(self) -> list[RawScreening]: ...
