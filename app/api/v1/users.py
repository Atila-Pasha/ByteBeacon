from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.telegram_connection_token import TelegramConnectionToken
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.telegram_service import (
    build_telegram_start_link,
    create_telegram_connection_token,
    disconnect_telegram_chat,
    get_user_telegram_status,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post(
    "/me/telegram/token",
    status_code=status.HTTP_201_CREATED,
)
async def create_telegram_token(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    token = await create_telegram_connection_token(db, current_user.id)
    result = await db.execute(
        select(TelegramConnectionToken)
        .where(TelegramConnectionToken.user_id == current_user.id)
        .order_by(TelegramConnectionToken.created_at.desc())
    )
    # Users can generate more than one link token. The query is ordered newest
    # first, so use that record instead of requiring exactly one row.
    token_record = result.scalars().first()
    expires_at = token_record.expires_at if token_record is not None else datetime.now(timezone.utc)
    return {
        "token": token,
        "telegram_link": build_telegram_start_link(token),
        "expires_at": expires_at.isoformat(),
    }


@router.get(
    "/me/telegram",
)
async def get_telegram_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_user_telegram_status(db, current_user.id)


@router.delete(
    "/me/telegram",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_telegram_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await disconnect_telegram_chat(db, current_user.id)
    return None
