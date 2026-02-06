"""
Security utilities for authentication.
Handles password hashing and JWT token management.
"""

from datetime import datetime, timedelta
from typing import Optional
import secrets
import hashlib

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# JWT settings
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_expire_minutes


def _prepare_password_for_bcrypt(password: str) -> bytes:
    """Pre-hash password with SHA256 to handle bcrypt's 72-byte limit."""
    # Always use SHA256 to normalize password length (bcrypt has a 72-byte hard limit)
    # This is a safe approach: https://security.stackexchange.com/questions/4781
    return hashlib.sha256(password.encode()).hexdigest().encode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash, handling bcrypt's 72-byte limit."""
    prepared_password = _prepare_password_for_bcrypt(plain_password)
    try:
        return bcrypt.checkpw(prepared_password, hashed_password.encode())
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password, handling bcrypt's 72-byte limit via pre-hashing."""
    prepared_password = _prepare_password_for_bcrypt(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password, salt)
    return hashed.decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """Generate a secure API key for flows."""
    return f"mk_{secrets.token_urlsafe(32)}"
