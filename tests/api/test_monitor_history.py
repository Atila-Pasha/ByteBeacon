from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1 import checks, incidents
from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.main import app


async def override_db():
    yield object()


def authenticated_client(monkeypatch):
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", False)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=1)
    return TestClient(app)


def clear_overrides():
    app.dependency_overrides.clear()


def test_get_checks_returns_newest_first_for_owned_monitor(monkeypatch):
    monitor = SimpleNamespace(id=12, user_id=1)
    newest = SimpleNamespace(
        id=2,
        monitor_id=12,
        status_code=200,
        latency=0.15,
        is_success=True,
        error=None,
        checked_at=datetime(2026, 8, 25, 12, tzinfo=timezone.utc),
    )
    oldest = SimpleNamespace(
        id=1,
        monitor_id=12,
        status_code=503,
        latency=0.2,
        is_success=False,
        error="HTTP 503",
        checked_at=datetime(2026, 8, 25, 11, tzinfo=timezone.utc),
    )

    async def get_monitor_by_id(**_kwargs):
        return monitor

    async def get_monitor_checks(_db, monitor_id):
        assert monitor_id == 12
        return [newest, oldest]

    monkeypatch.setattr(checks.monitor_service, "get_monitor_by_id", get_monitor_by_id)
    monkeypatch.setattr(checks.check_service, "get_monitor_checks", get_monitor_checks)

    with authenticated_client(monkeypatch) as client:
        response = client.get("/v1/monitors/12/checks")
    clear_overrides()

    assert response.status_code == 200
    assert [check["id"] for check in response.json()] == [2, 1]


def test_get_incidents_returns_empty_history_for_owned_monitor(monkeypatch):
    async def get_monitor_by_id(**_kwargs):
        return SimpleNamespace(id=12, user_id=1)

    async def get_monitor_incidents(_db, monitor_id):
        assert monitor_id == 12
        return []

    monkeypatch.setattr(incidents.monitor_service, "get_monitor_by_id", get_monitor_by_id)
    monkeypatch.setattr(
        incidents.incident_service,
        "get_monitor_incidents",
        get_monitor_incidents,
    )

    with authenticated_client(monkeypatch) as client:
        response = client.get("/v1/monitors/12/incidents")
    clear_overrides()

    assert response.status_code == 200
    assert response.json() == []


def test_monitor_history_returns_not_found_when_monitor_is_not_owned(monkeypatch):
    async def get_monitor_by_id(**_kwargs):
        return None

    monkeypatch.setattr(checks.monitor_service, "get_monitor_by_id", get_monitor_by_id)

    with authenticated_client(monkeypatch) as client:
        response = client.get("/v1/monitors/999/checks")
    clear_overrides()

    assert response.status_code == 404
    assert response.json() == {"detail": "Monitor not found"}


def test_monitor_history_requires_authentication(monkeypatch):
    monkeypatch.setattr(settings, "SCHEDULER_ENABLED", False)
    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as client:
        response = client.get("/v1/monitors/12/incidents")
    clear_overrides()

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
