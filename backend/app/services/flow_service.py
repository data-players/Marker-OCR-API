"""
Flow service for managing OCR extraction flows.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.logger import get_logger
from app.core.security import generate_api_key
from app.models.database_models import Flow, FlowExecution, Workspace

logger = get_logger(__name__)


class FlowService:
    """Service for flow operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_flow(
        self,
        workspace: Workspace,
        name: str,
        description: Optional[str] = None,
        extraction_schema: Optional[Dict[str, Any]] = None,
        introduction: str = "",
        ocr_options: Optional[Dict[str, Any]] = None
    ) -> Flow:
        """
        Create a new flow in a workspace.
        
        Args:
            workspace: Parent workspace
            name: Flow name
            description: Optional description
            extraction_schema: JSON schema for extraction
            introduction: LLM instructions
            ocr_options: OCR processing options
            
        Returns:
            Created flow
        """
        flow = Flow(
            workspace_id=workspace.id,
            name=name,
            description=description,
            api_key=generate_api_key(),
            extraction_schema=extraction_schema or {},
            introduction=introduction,
            ocr_options=ocr_options or {
                "output_format": "markdown",
                "force_ocr": False,
                "extract_images": False,
                "paginate_output": False
            }
        )
        
        self.db.add(flow)
        await self.db.flush()
        await self.db.refresh(flow)
        
        logger.info(f"Flow created: {flow.id} in workspace {workspace.id}")
        return flow
    
    async def get_workspace_flows(self, workspace: Workspace) -> List[Flow]:
        """
        Get all flows in a workspace.
        
        Args:
            workspace: Parent workspace
            
        Returns:
            List of flows
        """
        result = await self.db.execute(
            select(Flow)
            .where(Flow.workspace_id == workspace.id)
            .options(selectinload(Flow.executions))
            .order_by(Flow.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_flow(
        self,
        flow_id: str,
        workspace: Workspace
    ) -> Optional[Flow]:
        """
        Get a flow by ID, verifying it belongs to workspace.
        
        Args:
            flow_id: Flow ID
            workspace: Parent workspace
            
        Returns:
            Flow if found, None otherwise
        """
        result = await self.db.execute(
            select(Flow)
            .where(
                Flow.id == flow_id,
                Flow.workspace_id == workspace.id
            )
            .options(selectinload(Flow.executions))
        )
        return result.scalar_one_or_none()
    
    async def get_flow_by_api_key(self, api_key: str) -> Optional[Flow]:
        """
        Get a flow by its API key.
        
        Args:
            api_key: Flow API key
            
        Returns:
            Flow if found and active, None otherwise
        """
        result = await self.db.execute(
            select(Flow)
            .where(Flow.api_key == api_key, Flow.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def update_flow(
        self,
        flow: Flow,
        name: Optional[str] = None,
        description: Optional[str] = None,
        extraction_schema: Optional[Dict[str, Any]] = None,
        introduction: Optional[str] = None,
        ocr_options: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Flow:
        """
        Update flow properties.
        
        Args:
            flow: Flow to update
            name: New name
            description: New description
            extraction_schema: New schema
            introduction: New instructions
            ocr_options: New OCR options
            is_active: New active status
            
        Returns:
            Updated flow
        """
        if name is not None:
            flow.name = name
        if description is not None:
            flow.description = description
        if extraction_schema is not None:
            flow.extraction_schema = extraction_schema
        if introduction is not None:
            flow.introduction = introduction
        if ocr_options is not None:
            flow.ocr_options = ocr_options
        if is_active is not None:
            flow.is_active = is_active
        
        await self.db.flush()
        await self.db.refresh(flow, ["executions"])
        
        logger.info(f"Flow updated: {flow.id}")
        return flow
    
    async def regenerate_api_key(self, flow: Flow) -> Flow:
        """
        Regenerate the API key for a flow.
        
        Args:
            flow: Flow to update
            
        Returns:
            Flow with new API key
        """
        flow.api_key = generate_api_key()
        await self.db.flush()
        await self.db.refresh(flow, ["executions"])
        
        logger.info(f"Flow API key regenerated: {flow.id}")
        return flow
    
    async def delete_flow(self, flow: Flow) -> bool:
        """
        Delete a flow and all its executions.
        
        Args:
            flow: Flow to delete
            
        Returns:
            True if deleted
        """
        flow_id = flow.id
        await self.db.delete(flow)
        await self.db.flush()
        
        logger.info(f"Flow deleted: {flow_id}")
        return True
    
    async def create_execution(
        self,
        flow: Flow,
        input_type: str,
        input_source: str,
        file_path: Optional[str] = None
    ) -> FlowExecution:
        """
        Create a new execution record.
        
        Args:
            flow: Parent flow
            input_type: "url" or "file"
            input_source: URL or filename
            file_path: Optional stored file path
            
        Returns:
            Created execution
        """
        execution = FlowExecution(
            flow_id=flow.id,
            input_type=input_type,
            input_source=input_source,
            file_path=file_path,
            status="pending"
        )
        
        self.db.add(execution)
        await self.db.flush()
        await self.db.refresh(execution)
        
        logger.info(f"Execution created: {execution.id} for flow {flow.id}")
        return execution
    
    async def update_execution(
        self,
        execution: FlowExecution,
        status: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        processing_time: Optional[float] = None
    ) -> FlowExecution:
        """
        Update execution status and results.
        
        Args:
            execution: Execution to update
            status: New status
            extracted_data: Extracted data
            error_message: Error message if failed
            processing_time: Processing time
            
        Returns:
            Updated execution
        """
        execution.status = status
        
        if extracted_data is not None:
            execution.extracted_data = extracted_data
        if error_message is not None:
            execution.error_message = error_message
        if processing_time is not None:
            execution.processing_time = processing_time
        
        if status in ["completed", "failed"]:
            execution.completed_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(execution)
        
        logger.info(f"Execution updated: {execution.id} -> {status}")
        return execution
    
    async def get_execution(self, execution_id: str) -> Optional[FlowExecution]:
        """
        Get an execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution if found, None otherwise
        """
        result = await self.db.execute(
            select(FlowExecution).where(FlowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()
    
    async def get_flow_executions(
        self,
        flow: Flow,
        limit: int = 50,
        offset: int = 0
    ) -> List[FlowExecution]:
        """
        Get executions for a flow.
        
        Args:
            flow: Flow to get executions for
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of executions
        """
        result = await self.db.execute(
            select(FlowExecution)
            .where(FlowExecution.flow_id == flow.id)
            .order_by(FlowExecution.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_flow_execution_count(self, flow: Flow) -> int:
        """Get the number of executions for a flow."""
        result = await self.db.execute(
            select(func.count(FlowExecution.id))
            .where(FlowExecution.flow_id == flow.id)
        )
        return result.scalar_one()
