from fastapi import APIRouter, Depends

from app.api.deps import get_restaurant_recommendation_click_service
from app.schemas.restaurant import RestaurantRecommendationClickCreate
from app.services.restaurant_recommendation_click import RestaurantRecommendationClickService

router = APIRouter(prefix="/restaurant-recommendation-clicks", tags=["restaurant-recommendation-clicks"])


@router.post("", status_code=201)
async def create_restaurant_recommendation_click(
    body: RestaurantRecommendationClickCreate,
    service: RestaurantRecommendationClickService = Depends(get_restaurant_recommendation_click_service),
) -> None:
    await service.record(body.screening_id, body.restaurant_name, body.interest_type, body.outbound_click_id, body.place_id, body.place_metadata)
