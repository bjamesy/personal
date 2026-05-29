import re

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_screening_service
from app.schemas.screening import ScreeningResponse
from app.services.screening import ScreeningService

router = APIRouter(prefix="/screenings", tags=["screenings"])

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@router.get("/latest", response_model=list[ScreeningResponse])
async def list_upcoming_screenings(
    service: ScreeningService = Depends(get_screening_service),
) -> list[ScreeningResponse]:
    return await service.get_upcoming()


@router.get("", response_model=list[ScreeningResponse])
async def list_screenings_by_month(
    month: str = Query(description="Month in YYYY-MM format, e.g. 2026-05"),
    service: ScreeningService = Depends(get_screening_service),
) -> list[ScreeningResponse]:
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=422, detail="month must be in YYYY-MM format")
    year, m = map(int, month.split("-"))
    return await service.get_by_month(year, m)
