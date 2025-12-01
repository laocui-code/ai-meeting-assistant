"""
Database Configuration

This module contains the database connection configuration using SQLAlchemy 2.0
with async support. It provides the async engine, session factory, and base class
for all database models.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base for models
Base = declarative_base()


async def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function should be called at application startup.
    It imports all models to ensure they are registered with the Base metadata,
    then creates all tables that don't exist yet.
    """
    async with engine.begin() as conn:
        # Import models to register them with Base.metadata
        from app.models import action_item, meeting  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that provides a database session.

    This function is designed to be used with FastAPI's Depends() for
    dependency injection. It handles session lifecycle: creates a session,
    yields it for use, commits on success, rollbacks on exception, and
    always closes the session.

    Yields:
        AsyncSession: An async database session.

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

