"""
Authentication module.

Provides Supabase JWT validation, FastAPI security dependencies,
and role-based access control for the application.
"""

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.permissions import require_role

__all__ = [
    "get_current_user",
    "require_role",
]
