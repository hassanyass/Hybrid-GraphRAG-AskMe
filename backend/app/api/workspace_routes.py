"""
Workspace API routes.
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.dependencies import get_current_user
from backend.app.auth.schemas import AuthenticatedUser
from backend.app.database.session import get_db_session
from backend.app.models.workspace import Workspace
from backend.app.schemas.workspace_schema import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspaces"])


@router.get("/", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> List[Workspace]:
    """
    List all workspaces for the authenticated user.
    """
    stmt = (
        select(Workspace)
        .where(Workspace.user_id == current_user.id)
        .order_by(Workspace.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Workspace:
    """
    Create a new workspace.
    """
    workspace = Workspace(
        user_id=current_user.id,
        name=workspace_in.name,
        description=workspace_in.description,
    )
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> Workspace:
    """
    Get a specific workspace by ID.
    """
    stmt = select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found or unauthorized.",
        )
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """
    Delete a workspace and all its associated data (documents, conversations).
    """
    stmt = select(Workspace).where(
        Workspace.id == workspace_id,
        Workspace.user_id == current_user.id
    )
    result = await db.execute(stmt)
    workspace = result.scalar_one_or_none()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found or unauthorized.",
        )
        
    await db.delete(workspace)
    await db.commit()
