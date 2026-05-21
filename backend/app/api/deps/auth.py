"""Optional JWT bearer auth dependency."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings
from app.schemas.auth import AuthUserResponse
from app.services.auth_service import AuthCredentialsError, decode_access_token, get_user_by_id

_bearer = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthUserResponse | None:
    if not credentials or not settings.auth_enabled:
        return None
    try:
        payload = decode_access_token(settings, credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await get_user_by_id(settings, str(user_id))
    except AuthCredentialsError:
        return None


async def get_current_user_required(
    user: AuthUserResponse | None = Depends(get_current_user_optional),
) -> AuthUserResponse:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "status": "error",
                "error_code": "AUTH_REQUIRED",
                "message": "Authentication required.",
                "privacy_mode": "local-first",
            },
        )
    return user
