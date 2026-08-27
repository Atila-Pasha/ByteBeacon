from pydantic import BaseModel


class TelegramConnectRequest(BaseModel):
    token: str
    telegram_chat_id: int