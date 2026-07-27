"""
User API routes.

Protected endpoints for user profile management. All routes require
a valid Supabase JWT token via the ``get_current_user`` dependency.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.permissions import require_role
from backend.app.auth.schemas import AuthenticatedUser, MeResponse
from backend.app.database.session import get_db_session
from backend.app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


# ---------------------------------------------------------------------------
# Public-facing (authenticated) endpoints
# ---------------------------------------------------------------------------


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MeResponse:
    """
    Return the profile of the currently authenticated user.

    Requires a valid Bearer JWT in the ``Authorization`` header.
    """
    repo = UserRepository(db)
    user = await repo.get_by_supabase_id(current_user.supabase_user_id)

    return MeResponse(
        id=current_user.id,
        supabase_user_id=current_user.supabase_user_id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        authenticated=True,
        created_at=user.created_at if user else None,
        updated_at=user.updated_at if user else None,
    )


@router.get("/admin/check")
async def admin_check(
    current_user: AuthenticatedUser = Depends(require_role("ADMIN")),
) -> dict:
    """
    Admin-only endpoint to verify role-based access control.

    Returns a confirmation if the current user holds the ADMIN role.
    """
    return {
        "message": "Admin access granted.",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }
