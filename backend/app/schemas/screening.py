import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.theatre import TheatreResponse


class MovieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str


class ScreeningAttributeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    label: str
    category: str


class ScreeningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    theatre: TheatreResponse
    movie: MovieResponse
    start_time: datetime
    end_time: datetime | None
    raw_source_ref: str | None
    created_at: datetime
    attributes: list[ScreeningAttributeResponse]
