from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class MonitorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    url: HttpUrl
    interval: int = Field(gt=0)


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    url: HttpUrl | None = None
    interval: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class MonitorResponse(BaseModel):
    id: int
    user_id: int
    name: str
    url: HttpUrl
    interval: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)