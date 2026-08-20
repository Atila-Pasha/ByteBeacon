from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentResponse(BaseModel):
    id: int
    monitor_id: int
    status: str
    reason: str | None
    started_at: datetime
    resolved_at: datetime | None
    duration: float | None

    model_config = ConfigDict(from_attributes=True)