from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CheckResponse(BaseModel):
    id: int
    monitor_id: int
    status_code: int | None
    latency: float | None
    is_success: bool
    error: str | None
    checked_at: datetime

    model_config = ConfigDict(from_attributes=True)