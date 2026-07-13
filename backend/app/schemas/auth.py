"""Authentication request/response schemas."""

import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    remember: bool = False


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime, seconds


class AuthenticatedUser(BaseModel):
    id: uuid.UUID
    employee_code: str
    full_name: str
    email: EmailStr
    role: str
    department_id: uuid.UUID | None
    status: str


class LoginResponse(BaseModel):
    user: AuthenticatedUser
    tokens: TokenPair
