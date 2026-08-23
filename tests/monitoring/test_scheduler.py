import asyncio
from types import SimpleNamespace

import pytest

from app.monitoring import scheduler


class FakeResult:
    def __init__(self, monitors) -> None:
        self.monitors = monitors

    def scalars(self):
        return self

    def all(self):
        return self.monitors


class FakeSession:
    def __init__(self, monitors) -> None:
        self.monitors = monitors

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def execute(self, _query):
        return FakeResult(self.monitors)


class SessionFactory:
    def __init__(self, monitors) -> None:
        self.monitors = monitors
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return FakeSession(self.monitors)


@pytest.mark.asyncio
async def test_reconcile_only_starts_active_monitors(monkeypatch):
    active = SimpleNamespace(id=1, url="https://active.test", interval=1, is_active=True)
    factory = SessionFactory([active])
    scheduler_instance = scheduler.MonitorScheduler()
    started = asyncio.Event()

    async def fake_run_monitor(monitor):
        assert monitor is active
        started.set()
        await asyncio.Future()

    monkeypatch.setattr(scheduler, "AsyncSessionLocal", factory)
    monkeypatch.setattr(scheduler_instance, "_run_monitor", fake_run_monitor)

    await scheduler_instance._reconcile()
    await asyncio.wait_for(started.wait(), timeout=1)

    assert set(scheduler_instance._monitor_tasks) == {1}
    assert factory.calls == 1

    await scheduler_instance.stop()


@pytest.mark.asyncio
async def test_reconcile_restarts_changed_monitor(monkeypatch):
    monitor = SimpleNamespace(id=1, url="https://first.test", interval=1, is_active=True)
    factory = SessionFactory([monitor])
    scheduler_instance = scheduler.MonitorScheduler()
    cancelled = asyncio.Event()

    async def fake_run_monitor(_monitor):
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancelled.set()
            raise

    monkeypatch.setattr(scheduler, "AsyncSessionLocal", factory)
    monkeypatch.setattr(scheduler_instance, "_run_monitor", fake_run_monitor)

    await scheduler_instance._reconcile()
    first_task = scheduler_instance._monitor_tasks[1]
    await asyncio.sleep(0)

    monitor.url = "https://second.test"
    await scheduler_instance._reconcile()

    await asyncio.wait_for(cancelled.wait(), timeout=1)
    assert scheduler_instance._monitor_tasks[1] is not first_task

    await scheduler_instance.stop()


@pytest.mark.asyncio
async def test_run_monitor_uses_a_new_session_and_survives_check_failure(monkeypatch):
    monitor = SimpleNamespace(id=1, url="https://test", interval=1)
    factory = SessionFactory([])
    calls = 0
    checked = asyncio.Event()
    sleep_seconds = []

    async def fake_check(_db, _monitor):
        nonlocal calls
        calls += 1
        checked.set()
        if calls == 1:
            raise RuntimeError("temporary failure")

    async def fast_sleep(seconds):
        sleep_seconds.append(seconds)
        if calls >= 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(scheduler, "AsyncSessionLocal", factory)
    monkeypatch.setattr(scheduler, "check_monitor", fake_check)
    monkeypatch.setattr(scheduler.asyncio, "sleep", fast_sleep)

    with pytest.raises(asyncio.CancelledError):
        await scheduler.MonitorScheduler()._run_monitor(monitor)

    await asyncio.wait_for(checked.wait(), timeout=1)
    assert calls == 2
    assert factory.calls == 2
    assert sleep_seconds == [60, 60]