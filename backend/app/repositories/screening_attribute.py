import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening_attribute import ScreeningAttribute


class ScreeningAttributeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[ScreeningAttribute]:
        result = await self.session.execute(
            select(ScreeningAttribute).order_by(ScreeningAttribute.category, ScreeningAttribute.slug)
        )
        return list(result.scalars().all())

    async def get_or_create(self, category: str, slug: str, label: str) -> ScreeningAttribute:
        result = await self.session.execute(
            select(ScreeningAttribute).where(
                ScreeningAttribute.category == category,
                ScreeningAttribute.slug == slug,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        stmt = (
            pg_insert(ScreeningAttribute)
            .values(id=uuid.uuid4(), category=category, slug=slug, label=label)
            .on_conflict_do_nothing(constraint="uq_screening_attributes_category_slug")
            .returning(ScreeningAttribute)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row:
            return row

        # Lost the race — fetch the row inserted by the concurrent writer.
        result = await self.session.execute(
            select(ScreeningAttribute).where(
                ScreeningAttribute.category == category,
                ScreeningAttribute.slug == slug,
            )
        )
        attr = result.scalar_one_or_none()
        if attr is None:
            raise RuntimeError(
                f"Attribute ({category!r}, {slug!r}) vanished after concurrent insert; "
                "the concurrent writer may have rolled back."
            )
        return attr
