from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import Response

from app.api.deps import get_calendar_subscription_service
from app.config import settings
from app.schemas.calendar_subscription import (
    CalendarSubscriptionCreate,
    CalendarSubscriptionResponse,
)
from app.services.calendar_subscription import CalendarSubscriptionService

router = APIRouter(tags=["calendar"])


def _base_url(request: Request) -> str:
    if settings.public_base_url:
        return settings.public_base_url.rstrip("/")
    return str(request.base_url).rstrip("/")


@router.post("/calendar-subscriptions", response_model=CalendarSubscriptionResponse)
async def create_calendar_subscription(
    body: CalendarSubscriptionCreate,
    request: Request,
    service: CalendarSubscriptionService = Depends(get_calendar_subscription_service),
) -> CalendarSubscriptionResponse:
    subscription = await service.create(body.theatre_ids, body.label)
    feed_url = f"{_base_url(request)}/calendar/{subscription.token}.ics"
    return CalendarSubscriptionResponse(token=subscription.token, feed_url=feed_url)


@router.get("/calendar/{token}.ics")
async def get_calendar_feed(
    token: str,
    if_none_match: str | None = Header(default=None),
    service: CalendarSubscriptionService = Depends(get_calendar_subscription_service),
) -> Response:
    etag, ics = await service.build_ics(token, if_none_match)
    if etag is None:
        raise HTTPException(status_code=404, detail="Calendar feed not found")
    if ics is None:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": "no-cache"})
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": "inline; filename=screenings.ics",
            "ETag": etag,
            "Cache-Control": "no-cache",
        },
    )
