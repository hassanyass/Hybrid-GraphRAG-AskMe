"""
JWT handler.

Decodes and validates Supabase-issued JWT tokens. All secrets are
loaded from environment variables — nothing is hard-coded.
"""

import os
from datetime import datetime, timezone

import jwt

from backend.app.auth.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
)
from backend.app.auth.schemas import TokenPayload


# ---------------------------------------------------------------------------
# Configuration (loaded once at module import)
# ---------------------------------------------------------------------------

SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
JWT_ALGORITHM: str = "HS256"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate a Supabase JWT access token.

    Args:
        token: The raw JWT string from the Authorization header.

    Returns:
        A ``TokenPayload`` containing the validated claims.

    Raises:
        TokenExpiredError: If the token's ``exp`` claim is in the past.
        TokenInvalidError: If the token is malformed or the signature
            cannot be verified.
    """
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except (jwt.InvalidTokenError, jwt.DecodeError, Exception):
        raise TokenInvalidError()

    # Validate expiration defensively (belt-and-suspenders with PyJWT)
    exp = payload.get("exp")
    if exp is not None and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(tz=timezone.utc):
        raise TokenExpiredError()

    return TokenPayload(
        sub=payload.get("sub", ""),
        email=payload.get("email"),
        exp=payload.get("exp", 0),
        aud=payload.get("aud"),
        role=payload.get("role"),
    )
