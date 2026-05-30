import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_outbound_click_service
from app.schemas.outbound_click import OutboundClickCreate, OutboundClickPatch, OutboundClickResponse
from app.services.outbound_click import OutboundClickService

router = APIRouter(prefix="/outbound-clicks", tags=["outbound-clicks"])


@router.post("", response_model=OutboundClickResponse, status_code=201)
async def create_outbound_click(
    body: OutboundClickCreate,
    service: OutboundClickService = Depends(get_outbound_click_service),
) -> OutboundClickResponse:
    click = await service.record_click(body.screening_id, body.theatre_id)
    return OutboundClickResponse(
        id=click.id,
        screening_id=click.screening_id,
        theatre_id=click.theatre_id,
        clicked_at=click.clicked_at,
        ticket_confirmed=click.ticket_confirmed,
        prompted_at=click.prompted_at,
    )


@router.patch("/{click_id}", response_model=OutboundClickResponse)
async def patch_outbound_click(
    click_id: uuid.UUID,
    body: OutboundClickPatch,
    service: OutboundClickService = Depends(get_outbound_click_service),
) -> OutboundClickResponse:
    click = await service.record_response(click_id, body.ticket_confirmed, body.prompted_at)
    if click is None:
        raise HTTPException(status_code=404, detail="Outbound click not found")
    return OutboundClickResponse(
        id=click.id,
        screening_id=click.screening_id,
        theatre_id=click.theatre_id,
        clicked_at=click.clicked_at,
        ticket_confirmed=click.ticket_confirmed,
        prompted_at=click.prompted_at,
    )
