from types import SimpleNamespace

import pytest

from app.schemas.monitor import MonitorUpdate
from app.services import monitor_service


class FakeSession:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _monitor) -> None:
        return None


@pytest.mark.asyncio
async def test_update_monitor_ignores_explicit_null_values():
    session = FakeSession()
    monitor = SimpleNamespace(name="old", url="https://old.test", interval=5)
    update = MonitorUpdate(name=None, url=None, interval=10)

    result = await monitor_service.update_monitor(session, monitor, update)

    assert result is monitor
    assert monitor.name == "old"
    assert monitor.url == "https://old.test"
    assert monitor.interval == 10
    assert session.commits == 1