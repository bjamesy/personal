import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbound_click import OutboundClick, TicketConfirmedStatus


class OutboundClickRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, screening_id: uuid.UUID, theatre_id: uuid.UUID) -> OutboundClick:
        click = OutboundClick(screening_id=screening_id, theatre_id=theatre_id)
        self.session.add(click)
        await self.session.flush()
        await self.session.refresh(click)
        return click

    async def get(self, click_id: uuid.UUID) -> OutboundClick | None:
        result = await self.session.execute(
            select(OutboundClick).where(OutboundClick.id == click_id)
        )
        return result.scalar_one_or_none()

    async def patch(
        self,
        click: OutboundClick,
        ticket_confirmed: TicketConfirmedStatus | None,
        prompted_at: datetime | None,
    ) -> OutboundClick:
        if ticket_confirmed is not None:
            click.ticket_confirmed = ticket_confirmed
        if prompted_at is not None and click.prompted_at is None:
            click.prompted_at = prompted_at
        await self.session.flush()
        return click
