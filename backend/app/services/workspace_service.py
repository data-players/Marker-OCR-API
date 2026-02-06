"""
Workspace service for managing user workspaces.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.logger import get_logger
from app.models.database_models import Workspace, Flow, User

logger = get_logger(__name__)


class WorkspaceService:
    """Service for workspace operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_workspace(
        self,
        user: User,
        name: str,
        description: Optional[str] = None
    ) -> Workspace:
        """
        Create a new workspace for a user.
        
        Args:
            user: Owner user
            name: Workspace name
            description: Optional description
            
        Returns:
            Created workspace
        """
        workspace = Workspace(
            user_id=user.id,
            name=name,
            description=description
        )
        
        self.db.add(workspace)
        await self.db.flush()
        await self.db.refresh(workspace)
        
        logger.info(f"Workspace created: {workspace.id} for user {user.email}")
        return workspace
    
    async def get_user_workspaces(self, user: User) -> List[Workspace]:
        """
        Get all workspaces for a user.
        
        Args:
            user: Owner user
            
        Returns:
            List of workspaces with flow counts
        """
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.user_id == user.id)
            .options(selectinload(Workspace.flows))
            .order_by(Workspace.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_workspace(
        self,
        workspace_id: str,
        user: User
    ) -> Optional[Workspace]:
        """
        Get a workspace by ID, verifying ownership.
        
        Args:
            workspace_id: Workspace ID
            user: User requesting access
            
        Returns:
            Workspace if found and owned by user, None otherwise
        """
        result = await self.db.execute(
            select(Workspace)
            .where(
                Workspace.id == workspace_id,
                Workspace.user_id == user.id
            )
            .options(selectinload(Workspace.flows))
        )
        return result.scalar_one_or_none()
    
    async def update_workspace(
        self,
        workspace: Workspace,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Workspace:
        """
        Update workspace properties.
        
        Args:
            workspace: Workspace to update
            name: New name
            description: New description
            
        Returns:
            Updated workspace
        """
        if name is not None:
            workspace.name = name
        if description is not None:
            workspace.description = description
        
        await self.db.flush()
        await self.db.refresh(workspace)
        
        logger.info(f"Workspace updated: {workspace.id}")
        return workspace
    
    async def delete_workspace(self, workspace: Workspace) -> bool:
        """
        Delete a workspace and all its flows.
        
        Args:
            workspace: Workspace to delete
            
        Returns:
            True if deleted
        """
        workspace_id = workspace.id
        await self.db.delete(workspace)
        await self.db.flush()
        
        logger.info(f"Workspace deleted: {workspace_id}")
        return True
    
    async def get_workspace_flow_count(self, workspace: Workspace) -> int:
        """Get the number of flows in a workspace."""
        result = await self.db.execute(
            select(func.count(Flow.id))
            .where(Flow.workspace_id == workspace.id)
        )
        return result.scalar_one()
