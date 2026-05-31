import uuid

from pydantic import BaseModel

from app.models.restaurant_interest_event import RestaurantInterestType


class RestaurantResult(BaseModel):
    name: str
    rating: float | None
    address: str | None
    google_maps_url: str | None
    google_place_id: str | None
    google_place_metadata: dict | None


class RestaurantRecommendationClickCreate(BaseModel):
    theatre_id: uuid.UUID
    google_restaurant_name: str
    interest_type: RestaurantInterestType
    google_place_id: str | None = None
    google_place_metadata: dict | None = None
