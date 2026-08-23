from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.monitor import Monitor
from app.schemas.monitor import MonitorCreate, MonitorUpdate


async def create_monitor(
    db: AsyncSession,
    monitor_data: MonitorCreate,
    user_id: int,
) -> Monitor:
    monitor = Monitor(
        user_id=user_id,
        name=monitor_data.name,
        url=str(monitor_data.url),
        interval=monitor_data.interval,
    )

    db.add(monitor)

    await db.commit()
    await db.refresh(monitor)

    return monitor


async def get_monitor_by_id(
    db: AsyncSession,
    monitor_id: int,
    user_id: int,
) -> Monitor | None:
    result = await db.execute(
        select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == user_id,
        )
    )

    return result.scalar_one_or_none()


async def get_user_monitors(
    db: AsyncSession,
    user_id: int,
) -> list[Monitor]:
    result = await db.execute(
        select(Monitor)
        .where(Monitor.user_id == user_id)
    )

    return list(result.scalars().all())


async def update_monitor(
    db: AsyncSession,
    monitor: Monitor,
    monitor_data: MonitorUpdate,
) -> Monitor:
    update_data = monitor_data.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "url" in update_data and update_data["url"] is not None:
        update_data["url"] = str(update_data["url"])

    for field, value in update_data.items():
        setattr(monitor, field, value)

    await db.commit()
    await db.refresh(monitor)

    return monitor


async def delete_monitor(
    db: AsyncSession,
    monitor: Monitor,
) -> None:
    await db.delete(monitor)
    await db.commit()