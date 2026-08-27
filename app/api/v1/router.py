from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.monitors import router as monitor_router
from app.api.v1.users import router as user_router
from app.api.v1.auth import router as auth_router
from app.api.v1.checks import router as check_router
from app.api.v1.incidents import router as incident_router
from app.db.session import get_db
from app.schemas.telegram import TelegramConnectRequest
from app.services.telegram_service import TelegramConnectionError, connect_telegram_chat

router = APIRouter(
    prefix="/v1",
)


@router.post(
    "/telegram/connect",
    status_code=status.HTTP_200_OK,
)
async def connect_telegram_account(
    payload: TelegramConnectRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        await connect_telegram_chat(
            db,
            token=payload.token,
            telegram_chat_id=payload.telegram_chat_id,
        )
    except (TelegramConnectionError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return {"status": "connected"}


router.include_router(auth_router)
router.include_router(user_router)
router.include_router(monitor_router)
router.include_router(check_router)
router.include_router(incident_router)
