"""
Authentication Pydantic schemas.

Defines data contracts for authentication-related API responses.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TokenPayload(BaseModel):
    """Decoded JWT token payload from Supabase."""

    sub: str = Field(..., description="Supabase user ID (subject claim).")
    email: str | None = Field(None, description="User email from token.")
    exp: int = Field(..., description="Token expiration timestamp.")
    aud: str | None = Field(None, description="Token audience.")
    role: str | None = Field(None, description="Supabase role claim.")


class AuthenticatedUser(BaseModel):
    """Represents the currently authenticated user context."""

    id: uuid.UUID = Field(..., description="Application user UUID.")
    supabase_user_id: str = Field(..., description="Supabase Auth user ID.")
    email: str = Field(..., description="User email address.")
    username: str = Field(..., description="Display username.")
    role: str = Field(default="USER", description="Application role.")
    is_active: bool = Field(default=True, description="Account active status.")


class MeResponse(BaseModel):
    """Response schema for /users/me endpoint."""

    id: uuid.UUID
    supabase_user_id: str
    email: str
    username: str
    role: str
    is_active: bool
    authenticated: bool = True
    created_at: datetime
    updated_at: datetime
