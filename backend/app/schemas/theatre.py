import uuid

from pydantic import BaseModel, ConfigDict


class TheatreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    source_url: str
    is_cron_enabled: bool
