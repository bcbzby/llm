from datetime import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    nickname: str = Field(..., max_length=100)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenRefresh(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: str
    nickname: str
    role: str
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class RegisterOut(BaseModel):
    user_id: int
    email: str
    nickname: str
    role: str
    created_at: datetime


class LoginOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class TokenRefreshOut(BaseModel):
    access_token: str
    expires_in: int
