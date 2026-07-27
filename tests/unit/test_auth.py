"""
Authentication unit tests.

Tests JWT validation, token handling, and authentication dependency
logic without requiring a live database or Supabase connection.
"""

import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest

from backend.app.auth.exceptions import (
    AuthenticationError,
    InsufficientPermissionsError,
    MissingTokenError,
    TokenExpiredError,
    TokenInvalidError,
)
from backend.app.auth.jwt_handler import decode_access_token
from backend.app.auth.permissions import require_role
from backend.app.auth.schemas import AuthenticatedUser, TokenPayload


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

TEST_SECRET = "test-jwt-secret-for-unit-tests"
TEST_USER_ID = str(uuid.uuid4())
TEST_EMAIL = "testuser@example.com"


def _make_token(
    sub: str = TEST_USER_ID,
    email: str = TEST_EMAIL,
    exp: int | None = None,
    secret: str = TEST_SECRET,
    algorithm: str = "HS256",
) -> str:
    """Helper to generate a JWT token for testing."""
    payload = {
        "sub": sub,
        "email": email,
        "exp": exp or int(time.time()) + 3600,
        "aud": "authenticated",
        "role": "authenticated",
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


# ---------------------------------------------------------------------------
# JWT Decode Tests
# ---------------------------------------------------------------------------


class TestJWTDecoding:
    """Tests for the JWT handler decode_access_token function."""

    @patch("backend.app.auth.jwt_handler.SUPABASE_JWT_SECRET", TEST_SECRET)
    def test_valid_token_accepted(self):
        """A correctly signed, non-expired token should decode successfully."""
        token = _make_token()
        payload = decode_access_token(token)

        assert isinstance(payload, TokenPayload)
        assert payload.sub == TEST_USER_ID
        assert payload.email == TEST_EMAIL

    @patch("backend.app.auth.jwt_handler.SUPABASE_JWT_SECRET", TEST_SECRET)
    def test_expired_token_rejected(self):
        """An expired token should raise TokenExpiredError."""
        expired_time = int(time.time()) - 3600
        token = _make_token(exp=expired_time)

        with pytest.raises(TokenExpiredError):
            decode_access_token(token)

    @patch("backend.app.auth.jwt_handler.SUPABASE_JWT_SECRET", TEST_SECRET)
    def test_invalid_signature_rejected(self):
        """A token signed with a different secret should be rejected."""
        token = _make_token(secret="wrong-secret")

        with pytest.raises(TokenInvalidError):
            decode_access_token(token)

    @patch("backend.app.auth.jwt_handler.SUPABASE_JWT_SECRET", TEST_SECRET)
    def test_malformed_token_rejected(self):
        """A completely malformed string should raise TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            decode_access_token("not.a.valid.token")

    @patch("backend.app.auth.jwt_handler.SUPABASE_JWT_SECRET", TEST_SECRET)
    def test_empty_token_rejected(self):
        """An empty string should raise TokenInvalidError."""
        with pytest.raises(TokenInvalidError):
            decode_access_token("")


# ---------------------------------------------------------------------------
# Missing Token Tests
# ---------------------------------------------------------------------------


class TestMissingToken:
    """Tests for missing token handling."""

    def test_missing_token_exception_is_401(self):
        """MissingTokenError should produce a 401 status code."""
        error = MissingTokenError()
        assert error.status_code == 401

    def test_expired_token_exception_is_401(self):
        """TokenExpiredError should produce a 401 status code."""
        error = TokenExpiredError()
        assert error.status_code == 401

    def test_invalid_token_exception_is_401(self):
        """TokenInvalidError should produce a 401 status code."""
        error = TokenInvalidError()
        assert error.status_code == 401


# ---------------------------------------------------------------------------
# Role-Based Access Tests
# ---------------------------------------------------------------------------


class TestRoleBasedAccess:
    """Tests for the require_role dependency factory."""

    @pytest.mark.asyncio
    async def test_matching_role_passes(self):
        """A user with the required role should pass the check."""
        user = AuthenticatedUser(
            id=uuid.uuid4(),
            supabase_user_id=TEST_USER_ID,
            email=TEST_EMAIL,
            username="testuser",
            role="ADMIN",
            is_active=True,
        )

        checker = require_role("ADMIN")
        # Call the inner dependency directly with the user
        result = await checker(current_user=user)
        assert result.role == "ADMIN"

    @pytest.mark.asyncio
    async def test_mismatched_role_raises_403(self):
        """A user without the required role should get a 403."""
        user = AuthenticatedUser(
            id=uuid.uuid4(),
            supabase_user_id=TEST_USER_ID,
            email=TEST_EMAIL,
            username="testuser",
            role="USER",
            is_active=True,
        )

        checker = require_role("ADMIN")
        with pytest.raises(InsufficientPermissionsError):
            await checker(current_user=user)

    @pytest.mark.asyncio
    async def test_multiple_allowed_roles(self):
        """A user matching any of the allowed roles should pass."""
        user = AuthenticatedUser(
            id=uuid.uuid4(),
            supabase_user_id=TEST_USER_ID,
            email=TEST_EMAIL,
            username="testuser",
            role="ADMIN",
            is_active=True,
        )

        checker = require_role("USER", "ADMIN")
        result = await checker(current_user=user)
        assert result.role == "ADMIN"


# ---------------------------------------------------------------------------
# AuthenticatedUser Schema Tests
# ---------------------------------------------------------------------------


class TestAuthenticatedUserSchema:
    """Tests for the AuthenticatedUser Pydantic model."""

    def test_authenticated_user_creation(self):
        """AuthenticatedUser should be constructable with valid data."""
        user = AuthenticatedUser(
            id=uuid.uuid4(),
            supabase_user_id=TEST_USER_ID,
            email=TEST_EMAIL,
            username="testuser",
            role="USER",
            is_active=True,
        )
        assert user.email == TEST_EMAIL
        assert user.role == "USER"

    def test_default_role_is_user(self):
        """The default role should be USER."""
        user = AuthenticatedUser(
            id=uuid.uuid4(),
            supabase_user_id=TEST_USER_ID,
            email=TEST_EMAIL,
            username="testuser",
            is_active=True,
        )
        assert user.role == "USER"
