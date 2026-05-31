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
        screening_id: uuid.UUID,
        restaurant_name: str,
        interest_type: RestaurantInterestType,
        outbound_click_id: uuid.UUID | None = None,
        place_id: str | None = None,
        place_metadata: dict | None = None,
    ) -> RestaurantRecommendationClick:
        click = await self.repository.create(screening_id, restaurant_name, interest_type, outbound_click_id, place_id, place_metadata)
        await self.repository.session.commit()
        return click
