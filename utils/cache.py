"""
In-memory caching service with TTL support.

This module provides a simple caching mechanism for GitHub API responses
to minimize API calls and respect rate limits.
"""

from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Optional, TypeVar
import threading
import asyncio


T = TypeVar("T")


class CacheService:
    """
    In-memory cache with TTL (Time To Live) support.
    
    This implementation uses a dictionary to store cached values along with
    their expiration timestamps. It's designed to be Redis-ready for future
    migration to a distributed cache.
    """
    
    def __init__(self):
        """Initialize the cache with an empty storage dictionary and a lock for thread safety."""
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._lock = threading.Lock()
        # Coalesce concurrent cache misses for a key. This is deliberately kept
        # separate from the value cache: failures are never cached and a later
        # request can retry normally.
        self._inflight: dict[str, asyncio.Task[Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value if it exists and hasn't expired, None otherwise
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiration = self._cache[key]
            
            # Check if the cached value has expired
            if datetime.utcnow() > expiration:
                # Remove expired entry
                del self._cache[key]
                return None
            
            return value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        Store a value in the cache with a TTL.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time to live in seconds (default: 300 seconds / 5 minutes)
        """
        with self._lock:
            expiration = datetime.utcnow() + timedelta(seconds=ttl)
            self._cache[key] = (value, expiration)
    
    def invalidate(self, key: str) -> None:
        """
        Remove a value from the cache.
        
        Args:
            key: The cache key to invalidate
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()

    async def get_or_set_async(
        self,
        key: str,
        loader: Callable[[], Awaitable[T]],
        ttl: int = 300,
    ) -> T:
        """Return a cached value or load it once for all concurrent callers.

        A popular README image can cause many simultaneous requests for the
        same profile. Without single-flight behaviour, every request would make
        the same expensive GitHub GraphQL calls before the first response could
        populate the cache.
        """
        cached = self.get(key)
        if cached is not None:
            return cached

        task = self._inflight.get(key)
        if task is None:
            task = asyncio.create_task(loader())
            self._inflight[key] = task

        try:
            value = await task
        except Exception:
            raise
        else:
            self.set(key, value, ttl=ttl)
            return value
        finally:
            # Only remove the task this call observed. A completed task cannot
            # be replaced before this synchronous section runs, but the guard
            # keeps the behaviour correct if that ever changes.
            if self._inflight.get(key) is task and task.done():
                self._inflight.pop(key, None)
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from the cache.
        
        Returns:
            The number of expired entries removed
        """
        with self._lock:
            current_time = datetime.utcnow()
            expired_keys = [
                key for key, (_, expiration) in self._cache.items()
                if current_time > expiration
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    @staticmethod
    def generate_github_data_key(username: str) -> str:
        """
        Generate a cache key for GitHub data.
        
        Args:
            username: GitHub username
            
        Returns:
            Cache key in the format "github_data:{username}"
        """
        return f"github_data:{username}"
    
    @staticmethod
    def generate_contribution_key(username: str) -> str:
        """
        Generate a cache key for GitHub contribution data.
        
        Args:
            username: GitHub username
            
        Returns:
            Cache key in the format "github_contributions:{username}"
        """
        return f"github_contributions:{username}"
    
    @staticmethod
    def generate_activity_key(username: str) -> str:
        """
        Generate a cache key for GitHub activity data.
        
        Args:
            username: GitHub username
            
        Returns:
            Cache key in the format "github_activity:{username}"
        """
        return f"github_activity:{username}"

    @staticmethod
    def generate_profile_snapshot_key(username: str) -> str:
        """Generate a versioned cache key for a rich GitHub profile snapshot."""
        return f"github_profile_snapshot:v1:{username.strip().lower()}"
