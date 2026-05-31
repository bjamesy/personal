import uuid

from pydantic import BaseModel

from app.models.restaurant_interest_event import RestaurantInterestType


class RestaurantResult(BaseModel):
    name: str
    rating: float | None
    address: str | None
    google_maps_url: str | None


class RestaurantRecommendationClickCreate(BaseModel):
    theatre_id: uuid.UUID
    restaurant_name: str
    interest_type: RestaurantInterestType
