"""
Dependency injection for FastAPI application
"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
import redis.asyncio as redis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

# Configure structured logging
logger = structlog.get_logger()

# Database setup
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
    poolclass=StaticPool,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("Database error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """Redis client dependency"""
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        yield redis_client
    except Exception as e:
        logger.warning("Redis connection failed", error=str(e))
        # Return None if Redis is not available
        yield None
    finally:
        if 'redis_client' in locals():
            await redis_client.close()


def get_logger():
    """Logger dependency"""
    return logger


# Model dependencies (lazy loading)
_protein_encoder = None
_drug_encoder = None
_binding_predictor = None


def get_protein_encoder():
    """Protein encoder dependency (lazy loading)"""
    global _protein_encoder
    if _protein_encoder is None:
        from app.models.protein_encoder import ProteinEncoder
        _protein_encoder = ProteinEncoder()
        logger.info("Protein encoder loaded", model=settings.PROTEIN_MODEL)
    return _protein_encoder


def get_drug_encoder():
    """Drug encoder dependency (lazy loading)"""
    global _drug_encoder
    if _drug_encoder is None:
        from app.models.drug_encoder import DrugEncoder
        _drug_encoder = DrugEncoder()
        logger.info("Drug encoder loaded")
    return _drug_encoder


def get_binding_predictor():
    """Binding predictor dependency (lazy loading)"""
    global _binding_predictor
    if _binding_predictor is None:
        from app.models.binding_predictor import BindingPredictor
        protein_encoder = get_protein_encoder()
        drug_encoder = get_drug_encoder()
        _binding_predictor = BindingPredictor(protein_encoder, drug_encoder)
        logger.info("Binding predictor loaded")
    return _binding_predictor

