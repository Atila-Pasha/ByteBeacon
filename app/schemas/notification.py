from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    incident_id: int
    type: str
    status: str
    sent_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)