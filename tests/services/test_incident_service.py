from datetime import datetime
from types import SimpleNamespace

import pytest

from app.services.incident_service import reconcile_incident_for_check


class FakeResult:
    def __init__(self, incident) -> None:
        self.incident = incident

    def scalar_one_or_none(self):
        return self.incident


class FakeSession:
    def __init__(self, incident=None) -> None:
        self.incident = incident
        self.added = []

    async def execute(self, _query):
        return FakeResult(self.incident)

    def add(self, item) -> None:
        self.added.append(item)


@pytest.mark.asyncio
async def test_failed_check_opens_an_incident():
    session = FakeSession()
    check = SimpleNamespace(
        monitor_id=4,
        is_success=False,
        status_code=503,
        error=None,
    )

    incident = await reconcile_incident_for_check(session, check)

    assert incident is session.added[0]
    assert incident.monitor_id == 4
    assert incident.status == "open"
    assert incident.is_resolved is False
    assert incident.reason == "HTTP 503"
    assert isinstance(incident.started_at, datetime)


@pytest.mark.asyncio
async def test_failed_check_does_not_duplicate_an_open_incident():
    open_incident = SimpleNamespace()
    session = FakeSession(open_incident)
    check = SimpleNamespace(monitor_id=4, is_success=False, status_code=None, error="timeout")

    incident = await reconcile_incident_for_check(session, check)

    assert incident is open_incident
    assert session.added == []


@pytest.mark.asyncio
async def test_successful_check_resolves_the_open_incident():
    open_incident = SimpleNamespace(status="open", is_resolved=False, resolved_at=None)
    session = FakeSession(open_incident)
    check = SimpleNamespace(monitor_id=4, is_success=True, status_code=200, error=None)

    incident = await reconcile_incident_for_check(session, check)

    assert incident is open_incident
    assert incident.status == "resolved"
    assert incident.is_resolved is True
    assert isinstance(incident.resolved_at, datetime)
