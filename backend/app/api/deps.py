from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.outbound_click import OutboundClickService
from app.services.restaurant_interest_event import RestaurantInterestEventService
from app.services.restaurant_recommendation_click import RestaurantRecommendationClickService
from app.services.scraper_run import ScraperRunService
from app.services.screening import ScreeningService
from app.services.theatre import TheatreService


async def get_restaurant_recommendation_click_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[RestaurantRecommendationClickService, None]:
    yield RestaurantRecommendationClickService(session)


async def get_restaurant_interest_event_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[RestaurantInterestEventService, None]:
    yield RestaurantInterestEventService(session)


async def get_outbound_click_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[OutboundClickService, None]:
    yield OutboundClickService(session)


async def get_screening_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[ScreeningService, None]:
    yield ScreeningService(session)


async def get_theatre_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[TheatreService, None]:
    yield TheatreService(session)


async def get_scraper_run_service(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[ScraperRunService, None]:
    yield ScraperRunService(session)
