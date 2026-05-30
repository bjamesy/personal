import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.restaurant_interest_event import RestaurantInterestType


class RestaurantInterestEventCreate(BaseModel):
    outbound_click_id: uuid.UUID
    theatre_id: uuid.UUID
    interest_type: RestaurantInterestType


class RestaurantInterestEventResponse(BaseModel):
    id: uuid.UUID
    outbound_click_id: uuid.UUID
    theatre_id: uuid.UUID
    interest_type: RestaurantInterestType
    created_at: datetime
