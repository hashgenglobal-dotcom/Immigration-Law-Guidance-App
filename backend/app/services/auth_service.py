"""App user registration and JWT auth (POST-04)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext
from psycopg import errors as pg_errors
from psycopg.rows import dict_row

from app.core.config import Settings
from app.db.connection import connect, get_database_dsn
from app.schemas.auth import AuthTokenResponse, AuthUserResponse, LoginRequest, RegisterRequest

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


class AuthError(Exception):
    pass


class AuthConfigError(AuthError):
    pass


class AuthCredentialsError(AuthError):
    pass


def _require_jwt_secret(settings: Settings) -> str:
    if not settings.jwt_secret or settings.jwt_secret.strip() in (
        "",
        "change-me-in-production-use-openssl-rand-hex-32",
    ):
        if settings.app_env == "production":
            raise AuthConfigError("JWT_SECRET must be set in production")
    secret = settings.jwt_secret
    if not secret:
        secret = "dev-only-insecure-jwt-secret"
    return secret


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)


def create_access_token(*, settings: Settings, user_id: str, email: str) -> tuple[str, int]:
    secret = _require_jwt_secret(settings)
    minutes = settings.jwt_expire_minutes
    exp = datetime.now(UTC) + timedelta(minutes=minutes)
    payload = {"sub": user_id, "email": email, "exp": exp, "iat": datetime.now(UTC)}
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token, minutes


def decode_access_token(settings: Settings, token: str) -> dict:
    secret = _require_jwt_secret(settings)
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthCredentialsError("invalid token") from exc


async def register_user(settings: Settings, body: RegisterRequest) -> AuthTokenResponse:
    if not settings.auth_enabled:
        raise AuthConfigError("authentication is disabled")
    dsn = get_database_dsn(settings)
    email = body.email.lower().strip()
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(body.password)

    try:
        async with connect(settings) as conn:
            async with conn.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    """
                    INSERT INTO app_users (id, email, password_hash, display_name)
                    VALUES (%s::uuid, %s, %s, %s)
                    RETURNING id::text, email, display_name
                    """,
                    (user_id, email, pw_hash, body.display_name),
                )
                row = await cur.fetchone()
            await conn.commit()
    except pg_errors.UniqueViolation as exc:
        raise AuthError("email already registered") from exc

    if not row:
        raise AuthError("registration failed")

    token, minutes = create_access_token(
        settings=settings, user_id=row["id"], email=row["email"]
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in_minutes=minutes,
        user=AuthUserResponse(
            id=row["id"],
            email=row["email"],
            display_name=row.get("display_name"),
        ),
    )


async def login_user(settings: Settings, body: LoginRequest) -> AuthTokenResponse:
    if not settings.auth_enabled:
        raise AuthConfigError("authentication is disabled")
    email = body.email.lower().strip()

    async with connect(settings) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id::text, email, password_hash, display_name, is_active
                FROM app_users WHERE LOWER(email) = %s LIMIT 1
                """,
                (email,),
            )
            row = await cur.fetchone()

    if not row or not row["is_active"]:
        raise AuthCredentialsError("invalid credentials")
    if not verify_password(body.password, row["password_hash"]):
        raise AuthCredentialsError("invalid credentials")

    token, minutes = create_access_token(
        settings=settings, user_id=row["id"], email=row["email"]
    )
    return AuthTokenResponse(
        access_token=token,
        expires_in_minutes=minutes,
        user=AuthUserResponse(
            id=row["id"],
            email=row["email"],
            display_name=row.get("display_name"),
        ),
    )


async def get_user_by_id(settings: Settings, user_id: str) -> AuthUserResponse | None:
    async with connect(settings) as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id::text, email, display_name, is_active
                FROM app_users WHERE id = %s::uuid LIMIT 1
                """,
                (user_id,),
            )
            row = await cur.fetchone()
    if not row or not row["is_active"]:
        return None
    return AuthUserResponse(
        id=row["id"],
        email=row["email"],
        display_name=row.get("display_name"),
    )
