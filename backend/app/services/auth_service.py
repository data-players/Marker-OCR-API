"""
Authentication service for user management.
Handles registration, login, and user operations.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.logger import get_logger
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token
)
from app.models.database_models import User

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user(
        self, 
        email: str, 
        password: str, 
        name: str
    ) -> Optional[User]:
        """
        Register a new user.
        
        Args:
            email: User email
            password: Plain text password
            name: Display name
            
        Returns:
            Created user or None if email exists
        """
        # Check if email already exists
        existing = await self.get_user_by_email(email)
        if existing:
            logger.warning(f"Registration failed: email {email} already exists")
            return None
        
        # Create new user
        user = User(
            email=email.lower(),
            hashed_password=get_password_hash(password),
            name=name
        )
        
        try:
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            logger.info(f"User registered: {email}")
            return user
        except IntegrityError:
            await self.db.rollback()
            logger.error(f"Registration failed for {email}: integrity error")
            return None
    
    async def authenticate_user(
        self, 
        email: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User if authenticated, None otherwise
        """
        user = await self.get_user_by_email(email)
        
        if not user:
            logger.warning(f"Login failed: user {email} not found")
            return None
        
        if not user.is_active:
            logger.warning(f"Login failed: user {email} is inactive")
            return None
        
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Login failed: invalid password for {email}")
            return None
        
        logger.info(f"User authenticated: {email}")
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_user(
        self, 
        user: User, 
        name: Optional[str] = None, 
        password: Optional[str] = None
    ) -> User:
        """
        Update user profile.
        
        Args:
            user: User to update
            name: New display name
            password: New password
            
        Returns:
            Updated user
        """
        if name:
            user.name = name
        
        if password:
            user.hashed_password = get_password_hash(password)
        
        await self.db.flush()
        await self.db.refresh(user)
        logger.info(f"User updated: {user.email}")
        
        return user
    
    def create_user_token(self, user: User) -> str:
        """
        Create JWT token for user.
        
        Args:
            user: User to create token for
            
        Returns:
            JWT access token
        """
        return create_access_token(
            data={"sub": user.id, "email": user.email}
        )
