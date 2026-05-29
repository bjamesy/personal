import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_serializer

from app.models.scraper_run import ScraperRunStatus
from app.schemas.theatre import TheatreResponse


class ScraperRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    theatre: TheatreResponse
    started_at: datetime
    ended_at: datetime | None
    status: ScraperRunStatus | None
    items_extracted: int | None
    error_message: str | None

    @field_serializer("status")
    def serialize_status(self, value: ScraperRunStatus | None) -> str | None:
        return value.value if value else None
