from fastapi import APIRouter, Depends

from app.api.deps import get_theatre_service
from app.schemas.theatre import TheatreResponse
from app.services.theatre import TheatreService

router = APIRouter(prefix="/theatres", tags=["theatres"])


@router.get("", response_model=list[TheatreResponse])
async def list_theatres(
    service: TheatreService = Depends(get_theatre_service),
) -> list[TheatreResponse]:
    return await service.get_all()
