from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services import auth_service


class FakeResult:
    def __init__(self, token) -> None:
        self.token = token

    def scalar_one_or_none(self):
        return self.token


class FakeSession:
    def __init__(self, token) -> None:
        self.token = token
        self.commits = 0

    async def execute(self, _query):
        return FakeResult(self.token)

    async def commit(self) -> None:
        self.commits += 1


@pytest.mark.asyncio
async def test_rotate_refresh_token_revokes_expired_token():
    token = SimpleNamespace(
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        revoked_at=None,
    )
    session = FakeSession(token)

    result = await auth_service.rotate_refresh_token(session, "expired-token")

    assert result is None
    assert token.revoked_at is not None
    assert session.commits == 1