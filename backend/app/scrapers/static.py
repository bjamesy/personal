from abc import abstractmethod

import httpx

from app.scrapers.base import BaseScraper, RawScreening, ScraperStrategy


class StaticScraper(BaseScraper):
    strategy = ScraperStrategy.static

    _headers: dict[str, str] = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    async def scrape(self) -> list[RawScreening]:
        async with httpx.AsyncClient(
            follow_redirects=True, timeout=30.0, headers=self._headers
        ) as client:
            response = await client.get(self.config.source_url)
            response.raise_for_status()
        return self.parse(response.text)

    @abstractmethod
    def parse(self, html: str) -> list[RawScreening]: ...
