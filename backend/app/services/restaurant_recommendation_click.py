import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_interest_event import RestaurantInterestType
from app.models.restaurant_recommendation_click import RestaurantRecommendationClick
from app.repositories.restaurant_recommendation_click import RestaurantRecommendationClickRepository


class RestaurantRecommendationClickService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = RestaurantRecommendationClickRepository(session)

    async def record(
        self,
        theatre_id: uuid.UUID,
        restaurant_name: str,
        interest_type: RestaurantInterestType,
    ) -> RestaurantRecommendationClick:
        click = await self.repository.create(theatre_id, restaurant_name, interest_type)
        await self.repository.session.commit()
        return click
