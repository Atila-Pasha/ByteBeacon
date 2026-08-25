from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.check import Check


async def get_monitor_checks(
    db: AsyncSession,
    monitor_id: int,
) -> list[Check]:
    result = await db.execute(
        select(Check)
        .where(Check.monitor_id == monitor_id)
        .order_by(Check.checked_at.desc())
    )
    return list(result.scalars().all())
