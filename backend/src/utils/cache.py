"""
Redis cache utilities
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import json
import redis.asyncio as redis
from typing import Optional, Any
from functools import wraps
import hashlib

from src.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """
    Get Redis client singleton
    
    Returns:
        Redis client instance
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            await _redis_client.ping()
            logger.info("redis_connected", url=settings.REDIS_URL)
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            _redis_client = None
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("redis_disconnected")


async def get_cache(key: str) -> Optional[Any]:
    """
    Get value from cache
    
    Args:
        key: Cache key
    
    Returns:
        Cached value or None if not found/error
    """
    try:
        client = await get_redis()
        if not client:
            return None
        
        value = await client.get(key)
        if value:
            logger.debug("cache_hit", key=key)
            return json.loads(value)
        
        logger.debug("cache_miss", key=key)
        return None
    
    except Exception as e:
        logger.error("cache_get_error", key=key, error=str(e))
        return None


async def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Set value in cache
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: 300 = 5 min)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_redis()
        if not client:
            return False
        
        serialized = json.dumps(value)
        await client.setex(key, ttl, serialized)
        logger.debug("cache_set", key=key, ttl=ttl)
        return True
    
    except Exception as e:
        logger.error("cache_set_error", key=key, error=str(e))
        return False


async def delete_cache(key: str) -> bool:
    """
    Delete key from cache
    
    Args:
        key: Cache key
    
    Returns:
        True if deleted, False otherwise
    """
    try:
        client = await get_redis()
        if not client:
            return False
        
        await client.delete(key)
        logger.debug("cache_deleted", key=key)
        return True
    
    except Exception as e:
        logger.error("cache_delete_error", key=key, error=str(e))
        return False


async def delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching pattern
    
    Args:
        pattern: Pattern to match (e.g., "devices:*")
    
    Returns:
        Number of keys deleted
    """
    try:
        client = await get_redis()
        if not client:
            return 0
        
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            deleted = await client.delete(*keys)
            logger.info("cache_pattern_deleted", pattern=pattern, count=deleted)
            return deleted
        
        return 0
    
    except Exception as e:
        logger.error("cache_pattern_delete_error", pattern=pattern, error=str(e))
        return 0


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        MD5 hash of arguments
    """
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
    
    Example:
        @cached(ttl=60, key_prefix="devices")
        async def get_devices(blocked_only: bool = False):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await get_cache(cache_key_str)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await set_cache(cache_key_str, result, ttl)
            
            return result
        
        return wrapper
    return decorator
