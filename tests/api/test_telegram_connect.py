from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.v1 import router as api_router
from app.core.config import settings
from app.main import app


def test_telegram_connect_accepts_valid_request_body(monkeypatch):
    async def connect(_db, token, telegram_chat_id):
        assert token == "BB-TG-valid-token"
        assert telegram_chat_id == 123456789
        return SimpleNamespace(id=1)

    monkeypatch.setattr(api_router, "connect_telegram_chat", connect)
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")

    with TestClient(app) as client:
        response = client.post(
            "/v1/telegram/connect",
            json={
                "token": "BB-TG-valid-token",
                "telegram_chat_id": 123456789,
            },
        )

    assert response.status_code == 200
    assert response.json() == {"status": "connected"}


def test_telegram_connect_rejects_invalid_request_bodies(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_BOT_TOKEN", "")

    with TestClient(app) as client:
        missing_field = client.post(
            "/v1/telegram/connect",
            json={"token": "BB-TG-valid-token"},
        )
        wrong_type = client.post(
            "/v1/telegram/connect",
            json={
                "token": "BB-TG-valid-token",
                "telegram_chat_id": "not-an-integer",
            },
        )

    assert missing_field.status_code == 422
    assert wrong_type.status_code == 422


def test_telegram_connect_openapi_schema_describes_request_body():
    schema = app.openapi()
    request_schema = schema["paths"]["/v1/telegram/connect"]["post"]["requestBody"]

    assert request_schema["required"] is True
    assert request_schema["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/TelegramConnectRequest",
    }
    assert schema["components"]["schemas"]["TelegramConnectRequest"]["required"] == [
        "token",
        "telegram_chat_id",
    ]