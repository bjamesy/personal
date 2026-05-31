import uuid

from pydantic import BaseModel, Field, field_validator


class CalendarSubscriptionCreate(BaseModel):
    theatre_ids: list[uuid.UUID] = Field(min_length=1)
    label: str | None = Field(default=None, max_length=200)

    @field_validator("theatre_ids")
    @classmethod
    def deduplicate(cls, v: list[uuid.UUID]) -> list[uuid.UUID]:
        seen: set[uuid.UUID] = set()
        result = []
        for item in v:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result


class CalendarSubscriptionResponse(BaseModel):
    token: str
    feed_url: str
