"""
SQLAlchemy ORM models for database tables.
Defines User, Workspace, Flow, and FlowExecution entities.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, 
    Text, JSON, Float, Integer
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

from app.core.database import Base


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    workspaces: Mapped[List["Workspace"]] = relationship(
        "Workspace", back_populates="user", cascade="all, delete-orphan"
    )


class Workspace(Base):
    """Workspace model for organizing flows."""
    
    __tablename__ = "workspaces"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workspaces")
    flows: Mapped[List["Flow"]] = relationship(
        "Flow", back_populates="workspace", cascade="all, delete-orphan"
    )


class Flow(Base):
    """Flow model for OCR extraction pipelines."""
    
    __tablename__ = "flows"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    api_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    extraction_schema: Mapped[dict] = mapped_column(
        SQLiteJSON, nullable=False, default=dict
    )
    introduction: Mapped[str] = mapped_column(
        Text, nullable=False, default=""
    )
    ocr_options: Mapped[dict] = mapped_column(
        SQLiteJSON, nullable=False, default=dict
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace", back_populates="flows"
    )
    executions: Mapped[List["FlowExecution"]] = relationship(
        "FlowExecution", back_populates="flow", cascade="all, delete-orphan"
    )


class FlowExecution(Base):
    """FlowExecution model for tracking extraction history."""
    
    __tablename__ = "flow_executions"
    
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    flow_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("flows.id", ondelete="CASCADE"), nullable=False
    )
    input_type: Mapped[str] = mapped_column(
        String(20), nullable=False  # "url" or "file"
    )
    input_source: Mapped[str] = mapped_column(
        String(1024), nullable=False  # URL or filename
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True  # Stored file path
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    extracted_data: Mapped[Optional[dict]] = mapped_column(
        SQLiteJSON, nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    
    # Relationships
    flow: Mapped["Flow"] = relationship("Flow", back_populates="executions")
