from __future__ import annotations

from django.core.cache import cache

FIBER_LIST_CACHE_KEY = "fibers:list"


def invalidate_fiber_cache() -> None:
    """Clear cached fiber listings used in dashboards and APIs."""
    cache.delete(FIBER_LIST_CACHE_KEY)


__all__ = ["FIBER_LIST_CACHE_KEY", "invalidate_fiber_cache"]
