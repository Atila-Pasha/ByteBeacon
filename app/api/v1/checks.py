from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.check import CheckResponse
from app.services import check_service, monitor_service


router = APIRouter(
    prefix="/monitors/{monitor_id}/checks",
    tags=["Checks"],
)


@router.get("", response_model=list[CheckResponse])
async def get_monitor_checks(
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

    return await check_service.get_monitor_checks(db, monitor_id)
