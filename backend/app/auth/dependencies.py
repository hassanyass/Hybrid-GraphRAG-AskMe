"""
FastAPI authentication dependencies.

Provides injectable dependencies that extract and validate the JWT
token from incoming requests, then resolve the corresponding
application user from the database.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.exceptions import MissingTokenError
from backend.app.auth.jwt_handler import decode_access_token
from backend.app.auth.schemas import AuthenticatedUser, TokenPayload
from backend.app.database.session import get_db_session
from backend.app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# Security scheme — extracts Bearer token from Authorization header.
# auto_error=False so we can raise our own descriptive exceptions.
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Public dependencies
# ---------------------------------------------------------------------------


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
) -> AuthenticatedUser:
    """
    FastAPI dependency that validates the Supabase JWT and returns the
    authenticated application user.

    Flow:
        1. Extract Bearer token from ``Authorization`` header.
        2. Decode & validate JWT (signature, expiration).
        3. Look up the application user by ``supabase_user_id``.
        4. Return an ``AuthenticatedUser`` context object.

    Raises:
        MissingTokenError: No token supplied.
        TokenExpiredError / TokenInvalidError: Token validation failed.
        AuthenticationError: No matching application user found.
    """
    if credentials is None:
        raise MissingTokenError()

    token: str = credentials.credentials
    payload: TokenPayload = decode_access_token(token)

    # Resolve the application user from the database
    repo = UserRepository(db)
    user = await repo.get_by_supabase_id(payload.sub)

    if user is None:
        # Auto-provision: first-time login creates an application profile
        from backend.app.services.user_service import UserService

        service = UserService(db)
        user = await service.provision_user(
            supabase_user_id=payload.sub,
            email=payload.email or "",
        )

    if not user.is_active:
        from backend.app.auth.exceptions import AuthenticationError

        raise AuthenticationError(detail="User account is deactivated.")

    return AuthenticatedUser(
        id=user.id,
        supabase_user_id=user.supabase_user_id,
        email=user.email,
        username=user.username,
        role=user.role,
        is_active=user.is_active,
    )
