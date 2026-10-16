"""
Cache decorator for FastAPI endpoints
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import functools
import hashlib
import json
from typing import Callable
from fastapi import Request, Response
from src.utils.cache import get_cache, set_cache
import logging

logger = logging.getLogger(__name__)


def cache_endpoint(ttl: int = 60, key_prefix: str = "endpoint"):
    """
    Decorator to cache FastAPI endpoint responses
    
    Args:
        ttl: Time to live in seconds (default 60)
        key_prefix: Prefix for cache key (default "endpoint")
    
    Usage:
        @router.get("/users/")
        @cache_endpoint(ttl=120, key_prefix="users")
        async def get_users():
            return {"users": [...]}
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs if present
            request = kwargs.get('request')
            
            # Build cache key from function name + args + query params
            cache_key_parts = [key_prefix, func.__name__]
            
            # Add query params to key
            if request:
                query_params = dict(request.query_params)
                if query_params:
                    # Sort for consistent key
                    query_str = json.dumps(query_params, sort_keys=True)
                    cache_key_parts.append(query_str)
            
            # Hash for compact key
            cache_key_raw = ":".join(str(p) for p in cache_key_parts)
            cache_key = f"{key_prefix}:{hashlib.md5(cache_key_raw.encode()).hexdigest()}"
            
            # Try cache
            cached = await get_cache(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await set_cache(cache_key, result, ttl=ttl)
            logger.debug(f"Cache miss: {cache_key} (cached for {ttl}s)")
            
            return result
        
        return wrapper
    return decorator


def cache_response(ttl: int = 60, key_prefix: str = "response"):
    """
    Decorator to cache raw HTTP responses (for non-JSON endpoints)
    
    Usage:
        @router.get("/export")
        @cache_response(ttl=300, key_prefix="export")
        async def export_data():
            return Response(content=csv_data, media_type="text/csv")
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            
            # Build cache key
            cache_key_parts = [key_prefix, func.__name__]
            if request:
                query_params = dict(request.query_params)
                if query_params:
                    query_str = json.dumps(query_params, sort_keys=True)
                    cache_key_parts.append(query_str)
            
            cache_key_raw = ":".join(str(p) for p in cache_key_parts)
            cache_key = f"{key_prefix}:{hashlib.md5(cache_key_raw.encode()).hexdigest()}"
            
            # Try cache
            cached = await get_cache(cache_key)
            if cached is not None:
                return Response(
                    content=cached.get('content', ''),
                    media_type=cached.get('media_type', 'text/plain'),
                    headers=cached.get('headers', {})
                )
            
            # Execute
            result = await func(*args, **kwargs)
            
            # Cache response
            if isinstance(result, Response):
                cache_data = {
                    'content': result.body.decode() if isinstance(result.body, bytes) else result.body,
                    'media_type': result.media_type,
                    'headers': dict(result.headers)
                }
                await set_cache(cache_key, cache_data, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator
