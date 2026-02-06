"""
Workspace management routes.
CRUD operations for user workspaces.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.database_models import User
from app.models.workspace_models import (
    WorkspaceCreateRequest,
    WorkspaceUpdateRequest,
    WorkspaceResponse,
    WorkspaceListResponse
)
from app.services.workspace_service import WorkspaceService

logger = get_logger(__name__)

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def workspace_to_response(workspace, flow_count: int = None) -> WorkspaceResponse:
    """Convert workspace model to response."""
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        flow_count=flow_count if flow_count is not None else len(workspace.flows)
    )


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all workspaces for the current user."""
    service = WorkspaceService(db)
    workspaces = await service.get_user_workspaces(current_user)
    
    return WorkspaceListResponse(
        workspaces=[workspace_to_response(w) for w in workspaces],
        total=len(workspaces)
    )


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    request: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workspace."""
    service = WorkspaceService(db)
    
    workspace = await service.create_workspace(
        user=current_user,
        name=request.name,
        description=request.description
    )
    
    return workspace_to_response(workspace, flow_count=0)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific workspace."""
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id, current_user)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return workspace_to_response(workspace)


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    request: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a workspace."""
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id, current_user)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    updated = await service.update_workspace(
        workspace=workspace,
        name=request.name,
        description=request.description
    )
    
    return workspace_to_response(updated)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a workspace and all its flows."""
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id, current_user)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    await service.delete_workspace(workspace)
    return None
