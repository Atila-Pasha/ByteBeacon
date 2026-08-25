import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.telegram_connection_token import TelegramConnectionToken
from app.models.user import User


class TelegramConnectionError(ValueError):
    pass


def build_telegram_start_link(token: str) -> str:
    bot_username = settings.TELEGRAM_BOT_USERNAME.strip().lstrip("@")
    if not bot_username:
        raise TelegramConnectionError("Telegram bot username is not configured")
    return f"https://t.me/{bot_username}?start={quote(token, safe='')}"


def generate_telegram_token() -> str:
    raw = secrets.token_urlsafe(32)
    return f"BB-TG-{raw}"


def hash_telegram_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_telegram_connection_token(
    db: AsyncSession,
    user_id: int,
) -> str:
    token = generate_telegram_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.TELEGRAM_LINK_EXPIRE_MINUTES,
    )

    token_record = TelegramConnectionToken(
        user_id=user_id,
        token_hash=hash_telegram_token(token),
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.commit()
    await db.refresh(token_record)
    return token


async def connect_telegram_chat(
    db: AsyncSession,
    token: str,
    telegram_chat_id: int,
    user_id: int | None = None,
    expires_at: datetime | None = None,
) -> User:
    token_hash = hash_telegram_token(token)

    result = await db.execute(
        select(TelegramConnectionToken)
        .where(
            TelegramConnectionToken.token_hash == token_hash,
            TelegramConnectionToken.used_at.is_(None),
        )
        .with_for_update()
    )
    connection_token = result.scalar_one_or_none()

    if connection_token is None:
        raise TelegramConnectionError("Invalid or used connection token")

    effective_expiry = expires_at or connection_token.expires_at
    if effective_expiry <= datetime.now(timezone.utc):
        connection_token.used_at = datetime.now(timezone.utc)
        await db.commit()
        raise TelegramConnectionError("Connection token has expired")

    if user_id is not None and connection_token.user_id != user_id:
        raise TelegramConnectionError("This connection token does not belong to this user")

    result = await db.execute(select(User).where(User.id == connection_token.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise TelegramConnectionError("User not found")

    existing_result = await db.execute(
        select(User).where(User.telegram_chat_id == telegram_chat_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None and existing.id != user.id:
        raise TelegramConnectionError("This Telegram chat is already linked to another account")

    user.telegram_chat_id = telegram_chat_id
    connection_token.used_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)
    return user


async def disconnect_telegram_chat(
    db: AsyncSession,
    user_id: int,
) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return
    user.telegram_chat_id = None
    await db.commit()


async def get_user_telegram_status(
    db: AsyncSession,
    user_id: int,
) -> dict[str, str | int | bool | None]:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        return {"connected": False, "chat_id": None}
    return {
        "connected": user.telegram_chat_id is not None,
        "chat_id": user.telegram_chat_id,
    }
