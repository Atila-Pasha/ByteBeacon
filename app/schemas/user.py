from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    firstname: str = Field(min_length=1, max_length=100)
    lastname: str | None = Field(default=None, max_length=150)
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    firstname: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    lastname: str | None = Field(
        default=None,
        max_length=150,
    )
    email: EmailStr | None = None
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
    )


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime | None = None