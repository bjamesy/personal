import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_interest_event import RestaurantInterestType
from app.models.restaurant_recommendation_click import RestaurantRecommendationClick


class RestaurantRecommendationClickRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        theatre_id: uuid.UUID,
        google_restaurant_name: str,
        interest_type: RestaurantInterestType,
        google_place_id: str | None = None,
        google_place_metadata: dict | None = None,
    ) -> RestaurantRecommendationClick:
        click = RestaurantRecommendationClick(
            theatre_id=theatre_id,
            google_restaurant_name=google_restaurant_name,
            interest_type=interest_type,
            google_place_id=google_place_id,
            google_place_metadata=google_place_metadata,
        )
        self.session.add(click)
        await self.session.flush()
        return click
