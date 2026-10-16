"""
Tests for cache.py - Edge cases and error handling
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.utils.cache import (
    get_redis,
    get_cache,
    set_cache,
    delete_cache,
    delete_pattern,
    cache_key
)


@pytest.mark.asyncio
async def test_get_redis_singleton():
    """Test Redis client is singleton"""
    with patch('src.utils.cache.redis') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.from_url.return_value = mock_client
        
        client1 = await get_redis()
        client2 = await get_redis()
        
        assert client1 is client2
        # from_url called only once (singleton)
        mock_redis.from_url.assert_called_once()


@pytest.mark.asyncio
async def test_get_cache_miss():
    """Test cache miss returns None"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.get.return_value = None
        mock_get_redis.return_value = mock_client
        
        result = await get_cache("missing_key")
        assert result is None


@pytest.mark.asyncio
async def test_get_cache_hit():
    """Test cache hit returns parsed value"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.get.return_value = '{"data": "value"}'
        mock_get_redis.return_value = mock_client
        
        result = await get_cache("existing_key")
        assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_get_cache_error_handling():
    """Test cache get handles errors gracefully"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Redis error")
        mock_get_redis.return_value = mock_client
        
        result = await get_cache("key")
        assert result is None  # Error returns None


@pytest.mark.asyncio
async def test_set_cache_success():
    """Test cache set succeeds"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_get_redis.return_value = mock_client
        
        result = await set_cache("key", {"data": "value"}, ttl=60)
        assert result is True
        mock_client.setex.assert_called_once()


@pytest.mark.asyncio
async def test_set_cache_default_ttl():
    """Test cache set uses default TTL"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_get_redis.return_value = mock_client
        
        await set_cache("key", {"data": "value"})
        # Default TTL is 300
        args = mock_client.setex.call_args
        assert args[0][1] == 300  # TTL argument


@pytest.mark.asyncio
async def test_set_cache_error_handling():
    """Test cache set handles errors"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.setex.side_effect = Exception("Redis error")
        mock_get_redis.return_value = mock_client
        
        result = await set_cache("key", "value")
        assert result is False


@pytest.mark.asyncio
async def test_delete_cache_success():
    """Test cache delete succeeds"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_get_redis.return_value = mock_client
        
        result = await delete_cache("key")
        assert result is True
        mock_client.delete.assert_called_once_with("key")


@pytest.mark.asyncio
async def test_delete_cache_error():
    """Test cache delete handles errors"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.delete.side_effect = Exception("Error")
        mock_get_redis.return_value = mock_client
        
        result = await delete_cache("key")
        assert result is False


@pytest.mark.asyncio
async def test_delete_pattern_success():
    """Test pattern delete finds and deletes keys"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        
        # Mock scan_iter to return async iterator
        async def mock_scan():
            for key in ["devices:1", "devices:2"]:
                yield key
        
        mock_client.scan_iter.return_value = mock_scan()
        mock_client.delete.return_value = 2
        mock_get_redis.return_value = mock_client
        
        result = await delete_pattern("devices:*")
        assert result == 2


@pytest.mark.asyncio
async def test_delete_pattern_no_matches():
    """Test pattern delete with no matches"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        
        async def mock_scan():
            return
            yield  # Empty iterator
        
        mock_client.scan_iter.return_value = mock_scan()
        mock_get_redis.return_value = mock_client
        
        result = await delete_pattern("nomatch:*")
        assert result == 0


@pytest.mark.asyncio
async def test_delete_pattern_error():
    """Test pattern delete handles errors"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.scan_iter.side_effect = Exception("Error")
        mock_get_redis.return_value = mock_client
        
        result = await delete_pattern("pattern:*")
        assert result == 0


def test_cache_key_generation():
    """Test cache key generation from args"""
    key = cache_key("arg1", "arg2", kwarg1="value1")
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash length


def test_cache_key_deterministic():
    """Test cache key is deterministic"""
    key1 = cache_key("arg", kwarg="value")
    key2 = cache_key("arg", kwarg="value")
    assert key1 == key2


def test_cache_key_different_args():
    """Test different args produce different keys"""
    key1 = cache_key("arg1")
    key2 = cache_key("arg2")
    assert key1 != key2


@pytest.mark.asyncio
async def test_redis_connection_failure():
    """Test handling of Redis connection failure"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_get_redis.return_value = None
        
        result = await get_cache("key")
        assert result is None


@pytest.mark.asyncio
async def test_cache_json_serialization_error():
    """Test handling of JSON serialization errors"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_get_redis.return_value = mock_client
        
        # Object that can't be JSON serialized
        import datetime
        result = await set_cache("key", datetime.datetime.now())
        # Should handle error gracefully
        assert result is False


@pytest.mark.asyncio
async def test_cache_json_parse_error():
    """Test handling of invalid JSON in cache"""
    with patch('src.utils.cache.get_redis') as mock_get_redis:
        mock_client = AsyncMock()
        mock_client.get.return_value = "invalid json {"
        mock_get_redis.return_value = mock_client
        
        result = await get_cache("key")
        # Should handle parse error gracefully
        assert result is None
