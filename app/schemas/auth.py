from pydantic import BaseModel


class TokenResponse(BaseModel):
    message: str