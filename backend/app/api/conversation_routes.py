"""
Conversation API routes.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.schemas import AuthenticatedUser
from backend.app.database.session import get_db_session
from backend.app.models.conversation import Conversation
from backend.app.models.workspace import Workspace
from backend.app.schemas.conversation_schema import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["Conversations"])


@router.get("/workspace/{workspace_id}", response_model=List[ConversationResponse])
async def list_conversations(
    workspace_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[Conversation]:
    """
    List all conversations for a specific workspace.
    """
    # First verify workspace ownership
    ws_stmt = select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    )
    ws_result = await db.execute(ws_stmt)
    if not ws_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace.")

    stmt = (
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id)
        .order_by(Conversation.created_at.desc())
        .options(selectinload(Conversation.messages))
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conv_in: ConversationCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Conversation:
    """
    Create a new conversation in a workspace.
    """
    ws_stmt = select(Workspace).where(
        Workspace.id == conv_in.workspace_id,
        Workspace.user_id == current_user.id
    )
    ws_result = await db.execute(ws_stmt)
    if not ws_result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not authorized to access this workspace.")

    conversation = Conversation(
        user_id=current_user.id,
        workspace_id=conv_in.workspace_id,
        title=conv_in.title,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Conversation:
    """
    Get a specific conversation by ID.
    """
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).options(selectinload(Conversation.messages))
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or unauthorized.",
        )
    return conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a conversation.
    """
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or unauthorized.",
        )
        
    await db.delete(conversation)
    await db.commit()

@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: uuid.UUID,
    conv_in: ConversationUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Conversation:
    """
    Update a conversation (e.g. rename).
    """
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or unauthorized.",
        )
        
    if conv_in.title is not None:
        conversation.title = conv_in.title
        
    await db.commit()
    await db.refresh(conversation)
    
    return conversation
