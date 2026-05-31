import uuid

from pydantic import BaseModel

from app.models.restaurant_interest_event import RestaurantInterestType


class RestaurantResult(BaseModel):
    name: str
    rating: float | None
    address: str | None
    google_maps_url: str | None
    place_id: str | None
    place_metadata: dict | None


class RestaurantRecommendationClickCreate(BaseModel):
    screening_id: uuid.UUID
    outbound_click_id: uuid.UUID | None = None
    restaurant_name: str
    interest_type: RestaurantInterestType
    place_id: str | None = None
    place_metadata: dict | None = None
