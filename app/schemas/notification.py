from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    incident_id: int
    channel: str
    status: str
    error: str | None
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)
