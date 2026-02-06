"""
Database configuration using SQLAlchemy with SQLite.
Provides async database sessions for the application.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
from typing import Optional

from app.core.config import settings

# Database directory - lazy initialization
DB_DIR = Path(__file__).parent.parent.parent / "data"

# SQLite database URL
DATABASE_URL = f"sqlite+aiosqlite:///{DB_DIR}/marker.db"
SYNC_DATABASE_URL = f"sqlite:///{DB_DIR}/marker.db"

# Lazy engine initialization
_engine: Optional[object] = None
_sync_engine: Optional[object] = None
_async_session_maker: Optional[object] = None
_sync_session_maker: Optional[object] = None


def _ensure_db_dir():
    """Create database directory if it doesn't exist."""
    try:
        DB_DIR.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Read-only filesystem (e.g., in tests)
        pass


def get_engine():
    """Get or create async engine."""
    global _engine
    if _engine is None:
        _ensure_db_dir()
        _engine = create_async_engine(
            DATABASE_URL,
            echo=settings.debug,
            future=True
        )
    return _engine


def get_sync_engine():
    """Get or create sync engine."""
    global _sync_engine
    if _sync_engine is None:
        _ensure_db_dir()
        _sync_engine = create_engine(
            SYNC_DATABASE_URL,
            echo=settings.debug,
            future=True
        )
    return _sync_engine


def get_async_session_maker():
    """Get or create async session maker."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False
        )
    return _async_session_maker


def get_sync_session_maker():
    """Get or create sync session maker."""
    global _sync_session_maker
    if _sync_session_maker is None:
        _sync_session_maker = sessionmaker(
            get_sync_engine(),
            expire_on_commit=False
        )
    return _sync_session_maker


# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    Yields an async session and ensures cleanup.
    """
    async with get_async_session_maker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    _ensure_db_dir()
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database connections."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
