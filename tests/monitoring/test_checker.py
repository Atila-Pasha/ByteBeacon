from types import SimpleNamespace

import httpx
import pytest

from app.monitoring import checker


class FakeSession:
    def __init__(self) -> None:
        self.items = []
        self.commits = 0
        self.refreshed = []

    def add(self, item) -> None:
        self.items.append(item)

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, item) -> None:
        self.refreshed.append(item)


class ResponseClient:
    def __init__(self, response: httpx.Response | Exception) -> None:
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def get(self, _url: str):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.mark.asyncio
async def test_check_monitor_records_success(monkeypatch):
    session = FakeSession()
    monitor = SimpleNamespace(id=7, url="https://example.com")
    response = httpx.Response(204)

    monkeypatch.setattr(
        checker.httpx,
        "AsyncClient",
        lambda **_kwargs: ResponseClient(response),
    )

    check = await checker.check_monitor(session, monitor)

    assert check.monitor_id == 7
    assert check.status_code == 204
    assert check.is_success is True
    assert check.error is None
    assert check.latency >= 0
    assert session.items == [check]
    assert session.commits == 1
    assert session.refreshed == [check]


@pytest.mark.asyncio
async def test_check_monitor_records_http_failure(monkeypatch):
    session = FakeSession()
    monitor = SimpleNamespace(id=8, url="https://example.com")
    failure = httpx.ConnectError("connection failed")

    monkeypatch.setattr(
        checker.httpx,
        "AsyncClient",
        lambda **_kwargs: ResponseClient(failure),
    )

    check = await checker.check_monitor(session, monitor)

    assert check.monitor_id == 8
    assert check.status_code is None
    assert check.is_success is False
    assert check.error == "connection failed"
    assert session.commits == 1