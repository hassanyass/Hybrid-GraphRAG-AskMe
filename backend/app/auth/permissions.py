"""
Role-based access control (RBAC).

Provides a reusable FastAPI dependency factory for restricting
endpoints to users with specific roles.
"""

from fastapi import Depends

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.exceptions import InsufficientPermissionsError
from backend.app.auth.schemas import AuthenticatedUser


def require_role(*allowed_roles: str):
    """
    Return a FastAPI dependency that enforces role-based access.

    Usage::

        @router.get("/admin")
        async def admin_panel(
            user: AuthenticatedUser = Depends(require_role("ADMIN")),
        ):
            ...

    Args:
        *allowed_roles: One or more role strings the user must hold.

    Returns:
        A FastAPI-compatible dependency function.
    """

    async def _role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            raise InsufficientPermissionsError(
                detail=f"This action requires one of the following roles: "
                f"{', '.join(allowed_roles)}.",
            )
        return current_user

    return _role_checker
