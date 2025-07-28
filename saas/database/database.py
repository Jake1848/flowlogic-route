import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/flowlogic_saas"
)

ASYNC_DATABASE_URL = os.getenv(
    "ASYNC_DATABASE_URL",
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
)

# Create engines
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "options": "-c timezone=utc"
    }
)

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
    poolclass=NullPool,  # Use NullPool for async
)

# Create session makers
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False, 
    bind=engine
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def get_async_db():
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    from .models import Base
    
    async with async_engine.begin() as conn:
        # Import all models to ensure they're registered
        from . import models
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    if async_engine:
        await async_engine.dispose()
        logger.info("Database connections closed")


class DatabaseManager:
    """Database manager for handling connections and transactions"""
    
    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with AsyncSessionLocal() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_stats(self) -> dict:
        """Get database connection statistics"""
        try:
            pool = self.async_engine.pool
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid(),
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}


# Global database manager instance
db_manager = DatabaseManager()


# Utility functions for common database operations
async def execute_query(query: str, params: dict = None):
    """Execute a raw SQL query asynchronously"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(query, params or {})
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Query execution failed: {e}")
            raise


async def fetch_one(query: str, params: dict = None):
    """Fetch one result from a query"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(query, params or {})
            return result.fetchone()
        except Exception as e:
            logger.error(f"Fetch one failed: {e}")
            raise


async def fetch_all(query: str, params: dict = None):
    """Fetch all results from a query"""
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(query, params or {})
            return result.fetchall()
        except Exception as e:
            logger.error(f"Fetch all failed: {e}")
            raise