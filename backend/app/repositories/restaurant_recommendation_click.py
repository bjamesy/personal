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
        restaurant_name: str,
        interest_type: RestaurantInterestType,
    ) -> RestaurantRecommendationClick:
        click = RestaurantRecommendationClick(
            theatre_id=theatre_id,
            restaurant_name=restaurant_name,
            interest_type=interest_type,
        )
        self.session.add(click)
        await self.session.flush()
        return click
