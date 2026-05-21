"""Auth routes — POST-04."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps.auth import get_current_user_required
from app.core.config import Settings, get_settings
from app.schemas.auth import (
    AuthTokenResponse,
    AuthUserResponse,
    LoginRequest,
    RegisterRequest,
)
from app.services.auth_service import (
    AuthConfigError,
    AuthCredentialsError,
    AuthError,
    login_user,
    register_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
async def register(
    body: RegisterRequest,
    settings: Settings = Depends(get_settings),
) -> AuthTokenResponse:
    try:
        return await register_user(settings, body)
    except AuthConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except AuthError as exc:
        if "already" in str(exc).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "status": "error",
                    "error_code": "EMAIL_EXISTS",
                    "message": "An account with this email already exists.",
                    "privacy_mode": "local-first",
                },
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "error_code": "AUTH_ERROR",
                "message": "Registration failed.",
                "privacy_mode": "local-first",
            },
        ) from exc


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    settings: Settings = Depends(get_settings),
) -> AuthTokenResponse:
    try:
        return await login_user(settings, body)
    except AuthCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "error_code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
                "privacy_mode": "local-first",
            },
        ) from exc
    except AuthConfigError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/me", response_model=AuthUserResponse)
async def me(
    user: AuthUserResponse = Depends(get_current_user_required),
) -> AuthUserResponse:
    return user
