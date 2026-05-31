from fastapi import APIRouter, Depends

from app.api.deps import get_restaurant_interest_event_service
from app.schemas.restaurant_interest_event import (
    RestaurantInterestEventCreate,
    RestaurantInterestEventResponse,
)
from app.services.restaurant_interest_event import RestaurantInterestEventService

router = APIRouter(prefix="/restaurant-interest-events", tags=["restaurant-interest-events"])


@router.post("", response_model=RestaurantInterestEventResponse | None, status_code=201)
async def create_restaurant_interest_event(
    body: RestaurantInterestEventCreate,
    service: RestaurantInterestEventService = Depends(get_restaurant_interest_event_service),
) -> RestaurantInterestEventResponse | None:
    event = await service.record(body.outbound_click_id, body.interest_type)
    if event is None:
        return None
    return RestaurantInterestEventResponse(
        id=event.id,
        outbound_click_id=event.outbound_click_id,
        interest_type=event.interest_type,
        created_at=event.created_at,
    )
