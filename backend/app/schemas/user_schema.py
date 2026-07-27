"""
User Pydantic schemas.

Defines request/response data contracts for user-related API
operations. These schemas are independent of the ORM models.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr = Field(..., description="User email address.")
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Display username.",
    )


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: EmailStr | None = Field(None, description="Updated email address.")
    username: str | None = Field(
        None,
        min_length=3,
        max_length=100,
        description="Updated display username.",
    )
    is_active: bool | None = Field(None, description="Account active status.")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """Schema for returning user data in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
