import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant_interest_event import RestaurantInterestEvent, RestaurantInterestType


class RestaurantInterestEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_if_not_exists(
        self,
        outbound_click_id: uuid.UUID,
        interest_type: RestaurantInterestType,
    ) -> RestaurantInterestEvent | None:
        stmt = (
            pg_insert(RestaurantInterestEvent)
            .values(
                outbound_click_id=outbound_click_id,
                interest_type=interest_type,
            )
            .on_conflict_do_nothing(index_elements=["outbound_click_id"])
            .returning(RestaurantInterestEvent)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
