from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import UserCreate


async def register_user(
    db: AsyncSession,
    user_data: UserCreate,
) -> User:
    result = await db.execute(
        select(User).where(
            or_(
                User.email == user_data.email,
                User.username == user_data.username,
            )
        )
    )

    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.email == user_data.email:
            raise ValueError("Email already registered")

        raise ValueError("Username already taken")

    user = User(
        firstname=user_data.firstname,
        lastname=user_data.lastname,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    result = await db.execute(
        select(User).where(
            User.username == username,
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user


async def create_refresh_token_for_user(
    db: AsyncSession,
    user_id: int,
) -> str:
    raw_token = create_refresh_token()

    token_hash = hash_refresh_token(raw_token)

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(refresh_token)
    await db.commit()

    return raw_token



async def rotate_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> tuple[User, str] | None:

    token_hash = hash_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )

    refresh_token = result.scalar_one_or_none()

    if refresh_token is None:
        return None

    now = datetime.now(timezone.utc)

    if refresh_token.expires_at <= now:
        return None

    result = await db.execute(
        select(User).where(
            User.id == refresh_token.user_id,
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        return None

    # Revoke old refresh token
    refresh_token.revoked_at = now

    # Create new refresh token
    new_raw_token = create_refresh_token()

    new_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_token),
        expires_at=now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
    )

    db.add(new_token)

    await db.commit()

    return user, new_raw_token


async def revoke_refresh_token(
    db: AsyncSession,
    raw_token: str,
) -> None:
    token_hash = hash_refresh_token(raw_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )

    refresh_token = result.scalar_one_or_none()

    if refresh_token is None:
        return

    refresh_token.revoked_at = datetime.now(timezone.utc)

    await db.commit()