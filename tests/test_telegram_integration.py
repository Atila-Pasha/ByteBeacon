from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.bot.telegram_bot import TelegramBotService
from app.api.v1 import users as users_api
from app.services.telegram_service import (
    TelegramConnectionError,
    build_telegram_start_link,
    connect_telegram_chat,
    create_telegram_connection_token,
)


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeSession:
    def __init__(self, token_record=None, user_record=None, existing_user=None):
        self.token_record = token_record
        self.user_record = user_record
        self.existing_user = existing_user
        self.added = []
        self.commits = 0
        self.calls = 0

    async def execute(self, _query):
        self.calls += 1
        if self.calls == 1:
            return FakeResult(self.token_record)
        if self.calls == 2:
            return FakeResult(self.user_record)
        return FakeResult(self.existing_user)

    def add(self, item):
        self.added.append(item)

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        return None


@pytest.mark.asyncio
async def test_generate_telegram_connection_token_returns_short_lived_token():
    session = FakeSession()
    token = await create_telegram_connection_token(session, user_id=42)

    assert token.startswith("BB-TG-")
    assert len(token) > 12
    assert "BB-TG-" in token
    assert session.added


def test_build_telegram_start_link_uses_configured_bot_username(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_USERNAME", "@bytebeacon_bot")

    link = build_telegram_start_link("BB-TG-token_with_safe_chars")

    assert link == "https://t.me/bytebeacon_bot?start=BB-TG-token_with_safe_chars"


def test_build_telegram_start_link_requires_bot_username(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_USERNAME", "")

    with pytest.raises(TelegramConnectionError, match="username is not configured"):
        build_telegram_start_link("BB-TG-token")


@pytest.mark.asyncio
async def test_connect_telegram_chat_rejects_existing_chat_owned_by_another_user():
    token_record = SimpleNamespace(
        user_id=42,
        used_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    user_record = SimpleNamespace(id=42, telegram_chat_id=None)
    other_user = SimpleNamespace(id=9, telegram_chat_id=123456)
    session = FakeSession(token_record=token_record, user_record=user_record, existing_user=other_user)

    with pytest.raises(TelegramConnectionError, match="already linked"):
        await connect_telegram_chat(
            session,
            token="BB-TG-valid-token",
            telegram_chat_id=123456,
        )


@pytest.mark.asyncio
async def test_connect_telegram_chat_rejects_expired_token():
    token_record = SimpleNamespace(
        user_id=42,
        used_at=None,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    session = FakeSession(token_record=token_record, user_record=None, existing_user=None)

    with pytest.raises(TelegramConnectionError, match="expired"):
        await connect_telegram_chat(
            session,
            token="BB-TG-expired-token",
            telegram_chat_id=321,
        )


def test_telegram_settings_are_available():
    assert hasattr(settings, "TELEGRAM_BOT_TOKEN")
    assert hasattr(settings, "TELEGRAM_LINK_EXPIRE_MINUTES")
    assert hasattr(settings, "TELEGRAM_API_TIMEOUT")


@pytest.mark.asyncio
async def test_telegram_bot_stop_does_not_stop_a_poller_that_never_started():
    class Updater:
        async def stop(self):
            raise AssertionError("Updater.stop must not be called before polling starts")

    class Application:
        updater = Updater()

        async def shutdown(self):
            raise AssertionError("Application.shutdown must not be called before initialization")

    service = TelegramBotService()
    service.application = Application()

    await service.stop()

    assert service.application is None


@pytest.mark.asyncio
async def test_create_telegram_token_uses_the_newest_record_when_multiple_exist(monkeypatch):
    newest = SimpleNamespace(expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))

    class ResultWithManyTokens:
        def scalars(self):
            return self

        def first(self):
            return newest

    class TokenDatabase:
        async def execute(self, _query):
            return ResultWithManyTokens()

    async def create_token(_db, _user_id):
        return "BB-TG-new-token"

    monkeypatch.setattr(users_api, "create_telegram_connection_token", create_token)

    response = await users_api.create_telegram_token(
        db=TokenDatabase(),
        current_user=SimpleNamespace(id=42),
    )

    assert response["token"] == "BB-TG-new-token"
    assert response["expires_at"] == newest.expires_at.isoformat()
