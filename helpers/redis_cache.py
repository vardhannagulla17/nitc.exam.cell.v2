import os
import json
from datetime import datetime

# Lazy-initialized Redis client
_redis_client = None
_redis_available = None  # None = not yet checked

def _init_redis():
    """Initialize Upstash Redis client using Vercel marketplace-injected env vars."""
    global _redis_client, _redis_available

    if _redis_available is not None:
        return _redis_client

    # Vercel Upstash marketplace injects KV_REST_API_URL / KV_REST_API_TOKEN
    # upstash-redis SDK also accepts UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN
    url = (
        os.environ.get("KV_REST_API_URL") or
        os.environ.get("UPSTASH_REDIS_REST_URL")
    )
    token = (
        os.environ.get("KV_REST_API_TOKEN") or
        os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    )

    if url and token:
        try:
            from upstash_redis import Redis
            _redis_client = Redis(url=url, token=token)
            _redis_available = True
            print("✅ Upstash Redis cache connected (via Vercel integration)")
        except Exception as e:
            print(f"⚠️ Redis init failed, falling back to in-memory cache: {e}")
            _redis_available = False
    else:
        print("ℹ️ Redis env vars not set — using in-memory cache (set KV_REST_API_URL + KV_REST_API_TOKEN for Redis)")
        _redis_available = False

    return _redis_client


# In-memory fallback cache (used when Redis is unavailable)
_mem_cache = {}
_mem_timestamps = {}


def get_cached(cache_key, fetch_function, ttl_seconds=300):
    """
    Get data from cache. Uses Upstash Redis when available (shared across
    all Vercel serverless instances), otherwise falls back to in-memory.

    Args:
        cache_key: Unique string key
        fetch_function: Callable that returns fresh data on cache miss
        ttl_seconds: Time to live in seconds (default 5 minutes)
    """
    r = _init_redis()
    redis_key = f"nitc:{cache_key}"

    if r and _redis_available:
        try:
            raw = r.get(redis_key)
            if raw is not None:
                return json.loads(raw)
        except Exception as e:
            print(f"Redis get error for '{cache_key}': {e}")

        result = fetch_function()
        try:
            r.set(redis_key, json.dumps(result), ex=ttl_seconds)
        except Exception as e:
            print(f"Redis set error for '{cache_key}': {e}")
        return result

    # In-memory fallback
    now = datetime.now()
    if cache_key in _mem_cache:
        age = (now - _mem_timestamps[cache_key]).total_seconds()
        if age < ttl_seconds:
            return _mem_cache[cache_key]

    result = fetch_function()
    _mem_cache[cache_key] = result
    _mem_timestamps[cache_key] = now
    return result


def invalidate(cache_key):
    """Invalidate a specific cache key in both Redis and in-memory."""
    r = _init_redis()
    if r and _redis_available:
        try:
            r.delete(f"nitc:{cache_key}")
        except Exception as e:
            print(f"Redis delete error for '{cache_key}': {e}")
    _mem_cache.pop(cache_key, None)
    _mem_timestamps.pop(cache_key, None)


def invalidate_all():
    """Invalidate all nitc:* cache keys."""
    r = _init_redis()
    if r and _redis_available:
        try:
            keys = r.keys("nitc:*")
            if keys:
                r.delete(*keys)
        except Exception as e:
            print(f"Redis flush error: {e}")
    _mem_cache.clear()
    _mem_timestamps.clear()
