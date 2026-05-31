import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_interest_event import RestaurantInterestType
from app.models.restaurant_recommendation_click import RestaurantRecommendationClick


class RestaurantRecommendationClickRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        screening_id: uuid.UUID,
        restaurant_name: str,
        interest_type: RestaurantInterestType,
        outbound_click_id: uuid.UUID | None = None,
        place_id: str | None = None,
        place_metadata: dict | None = None,
    ) -> RestaurantRecommendationClick:
        click = RestaurantRecommendationClick(
            screening_id=screening_id,
            outbound_click_id=outbound_click_id,
            restaurant_name=restaurant_name,
            interest_type=interest_type,
            place_id=place_id,
            place_metadata=place_metadata,
        )
        self.session.add(click)
        await self.session.flush()
        return click
