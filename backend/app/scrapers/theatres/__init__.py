from app.scrapers.base import BaseScraper
from app.scrapers.theatres.fox import CONFIG as FOX_CONFIG, FoxScraper
from app.scrapers.theatres.hotdocs import CONFIG as HOTDOCS_CONFIG, HotDocsScraper
from app.scrapers.theatres.imagine_carlton import CONFIG as IMAGINE_CARLTON_CONFIG, ImagineCarItonScraper
from app.scrapers.theatres.kingsway import CONFIG as KINGSWAY_CONFIG, KingswayScraper
from app.scrapers.theatres.paradise import CONFIG as PARADISE_CONFIG, ParadiseScraper
from app.scrapers.theatres.revue import CONFIG as REVUE_CONFIG, RevueScraper
from app.scrapers.theatres.tops import CONFIG as TOPS_CONFIG, TOPSScraper

SCRAPERS: dict[str, BaseScraper] = {
    "paradise": ParadiseScraper(PARADISE_CONFIG),
    "hotdocs": HotDocsScraper(HOTDOCS_CONFIG),
    "imagine_carlton": ImagineCarItonScraper(IMAGINE_CARLTON_CONFIG),
    "tops": TOPSScraper(TOPS_CONFIG),
    "fox": FoxScraper(FOX_CONFIG),
    "revue": RevueScraper(REVUE_CONFIG),
    "kingsway": KingswayScraper(KINGSWAY_CONFIG),
}


def get_all_scrapers() -> list[BaseScraper]:
    return list(SCRAPERS.values())
