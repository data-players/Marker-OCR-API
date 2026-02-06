"""
Flow management routes.
CRUD operations for OCR extraction flows within workspaces.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.database_models import User, Workspace, Flow
from app.models.workspace_models import (
    FlowCreateRequest,
    FlowUpdateRequest,
    FlowResponse,
    FlowListResponse,
    FlowExecutionResponse,
    FlowExecutionListResponse
)
from app.services.workspace_service import WorkspaceService
from app.services.flow_service import FlowService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/workspaces/{workspace_id}/flows",
    tags=["flows"]
)


def flow_to_response(flow: Flow, execution_count: Optional[int] = None) -> FlowResponse:
    """Convert flow model to response."""
    # Use provided count or determine from loaded relationship
    if execution_count is None:
        # Only access executions if it's already loaded in the session
        try:
            execution_count = len(flow.executions)
        except Exception:
            # If executions aren't loaded, default to 0
            execution_count = 0
    
    return FlowResponse(
        id=flow.id,
        workspace_id=flow.workspace_id,
        name=flow.name,
        description=flow.description,
        api_key=flow.api_key,
        extraction_schema=flow.extraction_schema,
        introduction=flow.introduction,
        ocr_options=flow.ocr_options,
        is_active=flow.is_active,
        created_at=flow.created_at,
        updated_at=flow.updated_at,
        execution_count=execution_count
    )


async def get_workspace_for_user(
    workspace_id: str,
    current_user: User,
    db: AsyncSession
) -> Workspace:
    """Get workspace and verify ownership."""
    service = WorkspaceService(db)
    workspace = await service.get_workspace(workspace_id, current_user)
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return workspace


@router.get("", response_model=FlowListResponse)
async def list_flows(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all flows in a workspace."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flows = await flow_service.get_workspace_flows(workspace)
    
    return FlowListResponse(
        flows=[flow_to_response(f) for f in flows],
        total=len(flows)
    )


@router.post("", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    workspace_id: str,
    request: FlowCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new flow in the workspace."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flow = await flow_service.create_flow(
        workspace=workspace,
        name=request.name,
        description=request.description,
        extraction_schema=request.extraction_schema,
        introduction=request.introduction,
        ocr_options=request.ocr_options
    )
    
    return flow_to_response(flow, execution_count=0)


@router.get("/{flow_id}", response_model=FlowResponse)
async def get_flow(
    workspace_id: str,
    flow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific flow."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flow = await flow_service.get_flow(flow_id, workspace)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow not found"
        )
    
    return flow_to_response(flow)


@router.put("/{flow_id}", response_model=FlowResponse)
async def update_flow(
    workspace_id: str,
    flow_id: str,
    request: FlowUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a flow."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flow = await flow_service.get_flow(flow_id, workspace)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow not found"
        )
    
    updated = await flow_service.update_flow(
        flow=flow,
        name=request.name,
        description=request.description,
        extraction_schema=request.extraction_schema,
        introduction=request.introduction,
        ocr_options=request.ocr_options,
        is_active=request.is_active
    )
    
    return flow_to_response(updated)


@router.delete("/{flow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flow(
    workspace_id: str,
    flow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a flow and all its executions."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flow = await flow_service.get_flow(flow_id, workspace)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow not found"
        )
    
    await flow_service.delete_flow(flow)
    return None


@router.post("/{flow_id}/regenerate-key", response_model=FlowResponse)
async def regenerate_api_key(
    workspace_id: str,
    flow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate the API key for a flow."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flow = await flow_service.get_flow(flow_id, workspace)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow not found"
        )
    
    updated = await flow_service.regenerate_api_key(flow)
    return flow_to_response(updated)


@router.get("/{flow_id}/executions", response_model=FlowExecutionListResponse)
async def list_executions(
    workspace_id: str,
    flow_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get execution history for a flow."""
    workspace = await get_workspace_for_user(workspace_id, current_user, db)
    
    flow_service = FlowService(db)
    flow = await flow_service.get_flow(flow_id, workspace)
    
    if not flow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow not found"
        )
    
    executions = await flow_service.get_flow_executions(flow, limit, offset)
    total = await flow_service.get_flow_execution_count(flow)
    
    return FlowExecutionListResponse(
        executions=[
            FlowExecutionResponse(
                id=e.id,
                flow_id=e.flow_id,
                input_type=e.input_type,
                input_source=e.input_source,
                status=e.status,
                extracted_data=e.extracted_data,
                error_message=e.error_message,
                processing_time=e.processing_time,
                created_at=e.created_at,
                completed_at=e.completed_at
            )
            for e in executions
        ],
        total=total
    )
