"""Auth API schemas (POST-04)."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=120)

    @field_validator("password")
    @classmethod
    def password_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("password must not be empty")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class AuthUserResponse(BaseModel):
    id: str
    email: str
    display_name: str | None = None


class AuthTokenResponse(BaseModel):
    status: str = "ok"
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: AuthUserResponse
