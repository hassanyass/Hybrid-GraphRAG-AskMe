"""
Conversation repository.

Data access layer for Conversation and Message entities.
Encapsulates all conversation and message database queries.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.conversation import Conversation
from backend.app.models.message import Message
from backend.app.repositories.base_repository import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation CRUD and query operations."""

    model = Conversation

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        """Retrieve conversations belonging to a specific user."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_messages(
        self,
        conversation_id: uuid.UUID,
    ) -> Conversation | None:
        """Retrieve a conversation with all its messages eagerly loaded."""
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(self, message: Message) -> Message:
        """Add a message to a conversation."""
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Message]:
        """Retrieve paginated messages for a conversation."""
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
