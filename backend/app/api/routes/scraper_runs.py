from fastapi import APIRouter, Depends

from app.api.deps import get_scraper_run_service
from app.schemas.scraper_run import ScraperRunResponse
from app.services.scraper_run import ScraperRunService

router = APIRouter(prefix="/scraper-runs", tags=["scraper-runs"])


@router.get("", response_model=list[ScraperRunResponse])
async def list_latest_scraper_runs(
    service: ScraperRunService = Depends(get_scraper_run_service),
) -> list[ScraperRunResponse]:
    return await service.get_latest_per_theatre()
