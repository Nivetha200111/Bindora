"""
Caching utilities for performance optimization

Provides caching functionality using Redis for protein embeddings,
drug fingerprints, and other expensive computations.
"""
import asyncio
import json
import pickle
from typing import Any, Dict, Optional, Union
import structlog
import redis.asyncio as redis

logger = structlog.get_logger()

from app.config import settings


class Cache:
    """
    Async cache using Redis

    Args:
        redis_url: Redis connection URL
        default_ttl: Default time-to-live in seconds
    """

    def __init__(self, redis_url: str = settings.REDIS_URL, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._redis_client: Optional[redis.Redis] = None

    async def _get_client(self) -> Optional[redis.Redis]:
        """Get Redis client, creating if necessary"""
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}")
                return None

        return self._redis_client

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        client = await self._get_client()
        if not client:
            return None

        try:
            value = await client.get(key)
            if value:
                # Try to deserialize JSON first, then pickle
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        return pickle.loads(bytes.fromhex(value))
                    except Exception:
                        # Return as string if deserialization fails
                        return value

        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        client = await self._get_client()
        if not client:
            return False

        try:
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = pickle.dumps(value).hex()

            # Set in Redis
            await client.set(key, serialized, ex=ttl or self.default_ttl)

            logger.debug(f"Cached value", key=key, ttl=ttl or self.default_ttl)
            return True

        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key to delete

        Returns:
            True if successful, False otherwise
        """
        client = await self._get_client()
        if not client:
            return False

        try:
            await client.delete(key)
            logger.debug(f"Deleted cache key", key=key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        client = await self._get_client()
        if not client:
            return False

        try:
            return await client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {e}")
            return False

    async def clear(self) -> bool:
        """
        Clear all cache data

        Returns:
            True if successful, False otherwise
        """
        client = await self._get_client()
        if not client:
            return False

        try:
            await client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        client = await self._get_client()
        if not client:
            return {"available": False}

        try:
            info = await client.info("memory")
            return {
                "available": True,
                "memory_used": info.get("used_memory_human", "0B"),
                "memory_peak": info.get("used_memory_peak_human", "0B"),
                "keys": await client.dbsize()
            }
        except Exception as e:
            logger.warning(f"Cache stats failed: {e}")
            return {"available": False, "error": str(e)}


class EmbeddingCache:
    """
    Specialized cache for protein and drug embeddings

    Provides convenient methods for caching embeddings with
    appropriate key generation and serialization.
    """

    def __init__(self, cache: Cache):
        self.cache = cache

    def _make_protein_key(self, sequence: str) -> str:
        """Generate cache key for protein sequence"""
        # Use first 50 chars + length as key (to avoid very long keys)
        return f"protein_emb:{sequence[:50]}:{len(sequence)}"

    def _make_drug_key(self, smiles: str) -> str:
        """Generate cache key for drug SMILES"""
        return f"drug_emb:{hash(smiles) % 1000000}"  # Simple hash for SMILES

    async def get_protein_embedding(self, sequence: str) -> Optional[Any]:
        """Get cached protein embedding"""
        key = self._make_protein_key(sequence)
        return await self.cache.get(key)

    async def set_protein_embedding(self, sequence: str, embedding: Any) -> bool:
        """Cache protein embedding"""
        key = self._make_protein_key(sequence)
        return await self.cache.set(key, embedding, ttl=settings.CACHE_TTL)

    async def get_drug_embedding(self, smiles: str) -> Optional[Any]:
        """Get cached drug embedding"""
        key = self._make_drug_key(smiles)
        return await self.cache.get(key)

    async def set_drug_embedding(self, smiles: str, embedding: Any) -> bool:
        """Cache drug embedding"""
        key = self._make_drug_key(smiles)
        return await self.cache.set(key, embedding, ttl=settings.CACHE_TTL)


# Global cache instances
cache = Cache()
embedding_cache = EmbeddingCache(cache)


# Convenience functions
async def get_cached_protein_embedding(sequence: str) -> Optional[Any]:
    """Get cached protein embedding"""
    return await embedding_cache.get_protein_embedding(sequence)


async def set_cached_protein_embedding(sequence: str, embedding: Any) -> bool:
    """Cache protein embedding"""
    return await embedding_cache.set_protein_embedding(sequence, embedding)


async def get_cached_drug_embedding(smiles: str) -> Optional[Any]:
    """Get cached drug embedding"""
    return await embedding_cache.get_drug_embedding(smiles)


async def set_cached_drug_embedding(smiles: str, embedding: Any) -> bool:
    """Cache drug embedding"""
    return await embedding_cache.set_drug_embedding(smiles, embedding)

