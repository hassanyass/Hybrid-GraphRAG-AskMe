"""
User repository.

Data access layer for User entities. All database queries related
to users are encapsulated here — services never execute SQL directly.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.user import User
from backend.app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User CRUD and query operations."""

    model = User

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_supabase_id(self, supabase_user_id: str) -> User | None:
        """Find a user by their Supabase Auth user ID."""
        stmt = select(User).where(User.supabase_user_id == supabase_user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Find a user by their email address."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Find a user by their username."""
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Retrieve paginated list of active users only."""
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
