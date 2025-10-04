"""
Database connection and session management

Provides async database connection using SQLAlchemy with connection pooling
and proper error handling for production use.
"""
import structlog
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

logger = structlog.get_logger()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",  # Enable SQL logging in debug mode
    pool_size=20,  # Connection pool size
    max_overflow=30,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    future=True,  # Use SQLAlchemy 2.0 style
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,  # Manual transaction control
    autoflush=False,  # Manual flush control
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency for FastAPI

    Provides a database session with automatic cleanup and error handling.
    Sessions are automatically committed on success and rolled back on error.

    Yields:
        AsyncSession: Database session

    Raises:
        HTTPException: If database connection fails
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session created")
            yield session
            await session.commit()
            logger.debug("Database transaction committed")
        except Exception as e:
            await session.rollback()
            logger.error("Database transaction rolled back", error=str(e))
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")


async def test_database_connection() -> bool:
    """
    Test database connectivity

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            value = result.scalar()

            if value == 1:
                logger.info("Database connection test successful")
                return True
            else:
                logger.error("Database connection test failed - unexpected result")
                return False

    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False


async def create_tables():
    """
    Create all database tables

    Should be called during application startup or database migration.
    """
    try:
        from app.database.models import Base

        logger.info("Creating database tables")

        async with engine.begin() as conn:
            # Create all tables defined in models
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise


async def drop_tables():
    """
    Drop all database tables (for testing/reset)

    WARNING: This will delete all data!
    """
    try:
        from app.database.models import Base

        logger.warning("Dropping all database tables")

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("Database tables dropped")

    except Exception as e:
        logger.error("Failed to drop database tables", error=str(e))
        raise


async def get_database_info() -> dict:
    """
    Get database information and statistics

    Returns:
        dict: Database information including table counts
    """
    try:
        from app.database.models import Drug, Protein, Prediction, SearchQuery, SystemStats

        async with AsyncSessionLocal() as session:
            # Count records in each table
            drug_count = await session.scalar(
                "SELECT COUNT(*) FROM drugs"
            )
            protein_count = await session.scalar(
                "SELECT COUNT(*) FROM proteins"
            )
            prediction_count = await session.scalar(
                "SELECT COUNT(*) FROM predictions"
            )
            search_count = await session.scalar(
                "SELECT COUNT(*) FROM search_queries"
            )
            stats_count = await session.scalar(
                "SELECT COUNT(*) FROM system_stats"
            )

        return {
            "drugs": drug_count or 0,
            "proteins": protein_count or 0,
            "predictions": prediction_count or 0,
            "searches": search_count or 0,
            "system_stats": stats_count or 0,
            "database_url": settings.DATABASE_URL.replace(
                settings.DATABASE_URL.split('@')[0].split(':')[-1], '***'
            ) if '@' in settings.DATABASE_URL else "sqlite"
        }

    except Exception as e:
        logger.error("Failed to get database info", error=str(e))
        return {"error": str(e)}


# Database health check function
async def check_database_health() -> dict:
    """
    Comprehensive database health check

    Returns:
        dict: Health check results
    """
    health = {
        "status": "unknown",
        "connection": False,
        "tables_exist": False,
        "record_counts": {},
        "error": None
    }

    try:
        # Test basic connection
        health["connection"] = await test_database_connection()

        if health["connection"]:
            # Get table information
            health["record_counts"] = await get_database_info()

            # Check if tables exist and have data
            health["tables_exist"] = all(
                count > 0 for table, count in health["record_counts"].items()
                if table not in ["error"]
            )

        health["status"] = "healthy" if health["connection"] else "unhealthy"

    except Exception as e:
        health["status"] = "error"
        health["error"] = str(e)
        logger.error("Database health check failed", error=str(e))

    return health

