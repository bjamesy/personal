import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.outbound_click import TicketConfirmedStatus


class OutboundClickCreate(BaseModel):
    screening_id: uuid.UUID
    theatre_id: uuid.UUID


class OutboundClickPatch(BaseModel):
    ticket_confirmed: TicketConfirmedStatus | None = None
    prompted_at: datetime | None = None


class OutboundClickResponse(BaseModel):
    id: uuid.UUID
    screening_id: uuid.UUID
    theatre_id: uuid.UUID
    clicked_at: datetime
    ticket_confirmed: TicketConfirmedStatus | None
    prompted_at: datetime | None
