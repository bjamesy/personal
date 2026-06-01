from abc import abstractmethod

from playwright.async_api import async_playwright

from app.scrapers.base import BaseScraper, RawScreening, ScraperStrategy


class JSRenderedScraper(BaseScraper):
    strategy = ScraperStrategy.js_rendered
    wait_for_selector: str | None = None

    async def scrape(self) -> list[RawScreening]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await page.goto(self.config.source_url, wait_until="networkidle")
                if self.wait_for_selector:
                    await page.wait_for_selector(self.wait_for_selector, timeout=15000)
                html = await page.content()
            finally:
                await browser.close()
        return self.parse(html)

    @abstractmethod
    def parse(self, html: str) -> list[RawScreening]: ...
