import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_theatre_service
from app.schemas.restaurant import RestaurantResult
from app.services.google_places import INTENT_TYPES, fetch_nearby_restaurants
from app.services.theatre import TheatreService

router = APIRouter(tags=["restaurants"])


@router.get("/theatres/{theatre_id}/restaurants", response_model=list[RestaurantResult])
async def get_theatre_restaurants(
    theatre_id: uuid.UUID,
    intent: str = Query(...),
    service: TheatreService = Depends(get_theatre_service),
) -> list[RestaurantResult]:
    if intent not in INTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"intent must be one of: {', '.join(INTENT_TYPES)}")

    theatre = await service.get_by_id(theatre_id)
    if theatre is None:
        raise HTTPException(status_code=404, detail="Theatre not found")
    if theatre.latitude is None or theatre.longitude is None:
        raise HTTPException(status_code=400, detail="Theatre coordinates not available")

    results = await fetch_nearby_restaurants(
        str(theatre_id), theatre.latitude, theatre.longitude, intent
    )
    return [RestaurantResult(**r) for r in results]
