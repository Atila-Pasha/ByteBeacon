from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.monitor import (
    MonitorCreate,
    MonitorResponse,
    MonitorUpdate,
)

from app.services import monitor_service
from app.core.security import get_current_user


router = APIRouter(
    prefix="/monitors",
    tags=["Monitors"],
)


@router.post(
    "",
    response_model=MonitorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_monitor(
    monitor_data: MonitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await monitor_service.create_monitor(
        db=db,
        monitor_data=monitor_data,
        user_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[MonitorResponse],
)
async def get_monitors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await monitor_service.get_user_monitors(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{monitor_id}",
    response_model=MonitorResponse,
)
async def get_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    monitor = await monitor_service.get_monitor_by_id(
        db=db,
        monitor_id=monitor_id,
        user_id=current_user.id,
    )

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )

    return monitor


@router.patch(
    "/{monitor_id}",
    response_model=MonitorResponse,
)
async def update_monitor(
    monitor_id: int,
    monitor_data: MonitorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    monitor = await monitor_service.get_monitor_by_id(
        db=db,
        monitor_id=monitor_id,
        user_id=current_user.id,
    )

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )

    return await monitor_service.update_monitor(
        db=db,
        monitor=monitor,
        monitor_data=monitor_data,
    )


@router.delete(
    "/{monitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_monitor(
    monitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    monitor = await monitor_service.get_monitor_by_id(
        db=db,
        monitor_id=monitor_id,
        user_id=current_user.id,
    )

    if monitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitor not found",
        )

    await monitor_service.delete_monitor(
        db=db,
        monitor=monitor,
    )