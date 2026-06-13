"""Shared caching utility with cache-aside pattern.

Usage:
    from base.cache import cache_result, invalidate_cache

    @cache_result(ttl=300, key_prefix="speaker_profile")
    def get_speaker(slug):
        return SpeakerProfile.objects.get(slug=slug)
"""

import logging
from functools import wraps

from django.core.cache import cache

logger = logging.getLogger(__name__)

CACHE_TTL = {
    "speaker_profile": 300,
    "event_list": 60,
    "event_detail": 300,
    "tag_list": 600,
    "speaker_follow_count": 60,
    "user_org_membership": 300,
}

CACHE_KEY_PREFIX = "sw"


def _build_key(prefix: str, *args, **kwargs) -> str:
    """Build a consistent cache key.

    Pattern: ``sw:{prefix}:{arg1}:{arg2}:{key1=val1}``
    """
    parts = [CACHE_KEY_PREFIX, prefix]
    parts.extend(str(a) for a in args)
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(parts)


def cache_result(ttl=None, key_prefix=None):
    """Decorator: cache the return value using cache-aside pattern.

    Args:
        ttl: Time-to-live in seconds. Falls back to CACHE_TTL[key_prefix] or 60.
        key_prefix: Cache key prefix. Defaults to function name.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            prefix = key_prefix or func.__name__
            effective_ttl = ttl or CACHE_TTL.get(prefix, 60)
            cache_key = _build_key(prefix, *args, **kwargs)

            result = cache.get(cache_key)
            if result is not None:
                logger.debug("Cache HIT: %s", cache_key)
                return result

            logger.debug("Cache MISS: %s", cache_key)
            result = func(*args, **kwargs)
            try:
                cache.set(cache_key, result, effective_ttl)
            except Exception as e:
                logger.warning("Cache set failed for %s: %s", cache_key, e)
            return result

        return wrapper

    return decorator


def invalidate_cache(prefix: str, *args, **kwargs):
    """Delete a cached entry by its key prefix and arguments.

    Usage:
        invalidate_cache("speaker_profile", slug="some-slug")
    """
    cache_key = _build_key(prefix, *args, **kwargs)
    try:
        cache.delete(cache_key)
        logger.debug("Cache invalidated: %s", cache_key)
    except Exception as e:
        logger.warning("Cache delete failed for %s: %s", cache_key, e)


def invalidate_cache_pattern(pattern: str):
    """Delete all cache keys matching a pattern.

    Note: Requires Redis ``SCAN`` support. Falls back silently on unsupported backends.

    Usage:
        invalidate_cache_pattern("sw:speaker_profile:*")
    """
    try:
        client = cache.get_client(None) if hasattr(cache, "get_client") else None
        if client is None:
            logger.warning("Cache pattern invalidation not supported for this backend")
            return

        cursor = 0
        while True:
            cursor, keys = client.scan(cursor, match=pattern, count=100)
            if keys:
                client.delete(*keys)
            if cursor == 0:
                break
        logger.debug("Cache pattern invalidated: %s (keys: %d)", pattern, len(keys))
    except Exception as e:
        logger.warning("Cache pattern invalidation failed: %s", e)
