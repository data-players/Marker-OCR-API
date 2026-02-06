"""
Pydantic models for authentication requests and responses.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# Request Models

class UserRegisterRequest(BaseModel):
    """Request model for user registration."""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(
        min_length=8,
        description="Password (minimum 8 characters)"
    )
    name: str = Field(
        min_length=2,
        max_length=255,
        description="User display name"
    )


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    
    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password")


class UserUpdateRequest(BaseModel):
    """Request model for updating user profile."""
    
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="New display name"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        description="New password"
    )


# Response Models

class UserResponse(BaseModel):
    """Response model for user data."""
    
    id: str = Field(description="User ID")
    email: str = Field(description="User email")
    name: str = Field(description="User display name")
    is_active: bool = Field(description="Account active status")
    created_at: datetime = Field(description="Account creation date")
    
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Response model for authentication token."""
    
    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(description="User information")


class MessageResponse(BaseModel):
    """Simple message response."""
    
    message: str = Field(description="Response message")
