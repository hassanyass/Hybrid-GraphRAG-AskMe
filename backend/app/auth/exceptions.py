"""
Authentication exception classes.

Centralises all authentication and authorisation error types so that
error handling remains consistent across the application.
"""

from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Raised when a request cannot be authenticated."""

    def __init__(self, detail: str = "Could not validate credentials.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredError(AuthenticationError):
    """Raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__(detail="Token has expired.")


class TokenInvalidError(AuthenticationError):
    """Raised when a JWT token is malformed or signature is invalid."""

    def __init__(self) -> None:
        super().__init__(detail="Invalid authentication token.")


class MissingTokenError(AuthenticationError):
    """Raised when no Authorization header / token is provided."""

    def __init__(self) -> None:
        super().__init__(detail="Authentication token is missing.")


class InsufficientPermissionsError(HTTPException):
    """Raised when the user lacks the required role or permission."""

    def __init__(self, detail: str = "Insufficient permissions.") -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
