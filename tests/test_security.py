from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.main import app


class FakeResult:
    def scalar_one_or_none(self):
        return make_user()


class FakeSession:
    async def execute(self, _query):
        return FakeResult()


async def override_db():
    yield FakeSession()


def make_user():
    return SimpleNamespace(
        id=1,
        firstname="Test",
        lastname="User",
        email="test@example.com",
        username="testuser",
        created_at=datetime.now(timezone.utc),
        updated_at=None,
    )


@pytest.mark.asyncio
async def test_get_current_user_accepts_bearer_header(monkeypatch):
    monkeypatch.setattr(
        security,
        "decode_access_token",
        lambda token: {"type": "access", "sub": "1"},
    )

    user = await security.get_current_user(
        authorization="Bearer header-token",
        access_token=None,
        db=FakeSession(),
    )

    assert user.id == 1


@pytest.mark.asyncio
async def test_get_current_user_falls_back_to_cookie(monkeypatch):
    seen_tokens = []

    def decode(token):
        seen_tokens.append(token)
        return {"type": "access", "sub": "1"}

    monkeypatch.setattr(security, "decode_access_token", decode)

    await security.get_current_user(
        authorization=None,
        access_token="cookie-token",
        db=FakeSession(),
    )

    assert seen_tokens == ["cookie-token"]


@pytest.mark.asyncio
async def test_get_current_user_header_takes_precedence_over_cookie(monkeypatch):
    seen_tokens = []

    def decode(token):
        seen_tokens.append(token)
        return {"type": "access", "sub": "1"}

    monkeypatch.setattr(security, "decode_access_token", decode)

    await security.get_current_user(
        authorization="Bearer header-token",
        access_token="cookie-token",
        db=FakeSession(),
    )

    assert seen_tokens == ["header-token"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "authorization",
    ["Basic credentials", "Bearer", "Bearer ", "Bearer one two", ""],
)
async def test_get_current_user_rejects_malformed_authorization(authorization):
    with pytest.raises(HTTPException) as exception:
        await security.get_current_user(
            authorization=authorization,
            access_token="cookie-token",
            db=FakeSession(),
        )

    assert exception.value.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "authorization,access_token",
    [(None, None), ("Bearer invalid", None), (None, "invalid")],
)
async def test_get_current_user_rejects_missing_or_invalid_tokens(
    monkeypatch,
    authorization,
    access_token,
):
    def reject(_token):
        raise jwt.InvalidTokenError

    monkeypatch.setattr(security, "decode_access_token", reject)

    with pytest.raises(HTTPException) as exception:
        await security.get_current_user(
            authorization=authorization,
            access_token=access_token,
            db=FakeSession(),
        )

    assert exception.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_rejects_expired_access_token():
    expired_token = jwt.encode(
        {
            "sub": "1",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    with pytest.raises(HTTPException) as exception:
        await security.get_current_user(
            authorization=f"Bearer {expired_token}",
            access_token=None,
            db=FakeSession(),
        )

    assert exception.value.status_code == 401


def test_current_user_route_accepts_header_and_cookie_with_header_precedence(monkeypatch):
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", False)
    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as client:
        header_token = security.create_access_token(user_id=1)
        response = client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {header_token}"},
            cookies={"access_token": "invalid-cookie-token"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == 1