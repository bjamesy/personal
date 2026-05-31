import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbound_click import OutboundClick, TicketConfirmedStatus
from app.repositories.outbound_click import OutboundClickRepository


class OutboundClickService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = OutboundClickRepository(session)

    async def record_click(self, screening_id: uuid.UUID) -> OutboundClick:
        click = await self.repository.create(screening_id)
        await self.repository.session.commit()
        return click

    async def record_response(
        self,
        click_id: uuid.UUID,
        ticket_confirmed: TicketConfirmedStatus | None,
        prompted_at: datetime | None,
    ) -> OutboundClick | None:
        click = await self.repository.get(click_id)
        if click is None:
            return None
        click = await self.repository.patch(click, ticket_confirmed, prompted_at)
        await self.repository.session.commit()
        return click
