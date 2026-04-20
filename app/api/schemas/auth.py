from datetime import datetime
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    login: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class LoginResponse(BaseModel):
    message: str
    user_id: str
    login: str
    role: str


class UserResponse(BaseModel):
    id: str
    login: str
    role: str
    is_active: bool
    created_at: datetime