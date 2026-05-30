import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_interest_event import RestaurantInterestEvent, RestaurantInterestType
from app.repositories.restaurant_interest_event import RestaurantInterestEventRepository


class RestaurantInterestEventService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = RestaurantInterestEventRepository(session)

    async def record(
        self,
        outbound_click_id: uuid.UUID,
        theatre_id: uuid.UUID,
        interest_type: RestaurantInterestType,
    ) -> RestaurantInterestEvent | None:
        event = await self.repository.create_if_not_exists(
            outbound_click_id, theatre_id, interest_type
        )
        await self.repository.session.commit()
        return event
