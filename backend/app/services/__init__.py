from backend.app.services.document_service import DocumentService
from backend.app.services.user_service import UserService

__all__ = ["UserService", "DocumentService"]

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.repositories.user_repository import UserRepository


class UserService:
    """Orchestrates user-related business operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepository(session)

    async def provision_user(
        self,
        *,
        supabase_user_id: str,
        email: str,
    ) -> User:
        """
        Create an application user profile for a newly authenticated
        Supabase user (auto-provisioning on first login).

        The username defaults to the email prefix to avoid requiring
        an extra registration step. The user can update it later.

        Args:
            supabase_user_id: The ``sub`` claim from the JWT.
            email: The email address from the JWT.

        Returns:
            The newly created User entity.
        """
        # Derive a default username from the email prefix
        username = email.split("@")[0] if email else supabase_user_id[:20]

        user = User(
            supabase_user_id=supabase_user_id,
            email=email,
            username=username,
            role="USER",
        )

        return await self._repo.create(user)

    async def get_user_by_id(self, user_id) -> User | None:
        """Retrieve a user by their application UUID."""
        return await self._repo.get_by_id(user_id)

    async def get_user_by_supabase_id(self, supabase_user_id: str) -> User | None:
        """Retrieve a user by their Supabase Auth user ID."""
        return await self._repo.get_by_supabase_id(supabase_user_id)

    async def update_profile(
        self,
        user: User,
        *,
        username: str | None = None,
        email: str | None = None,
    ) -> User:
        """
        Update a user's mutable profile fields.

        Only non-None parameters are applied.

        Args:
            user: The User entity to update.
            username: Optional new username.
            email: Optional new email.

        Returns:
            The updated User entity.
        """
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email

        return await self._repo.update(user)
