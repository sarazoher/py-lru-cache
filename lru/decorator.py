"""``@lru_cached(capacity)``: memoise a function with LRUCache, like functools.lru_cache."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from .cache import LRUCache

P = ParamSpec("P")
R = TypeVar("R")
_MISS = object()


def lru_cached(capacity: int = 128) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorate(func: Callable[P, R]) -> Callable[P, R]:
        cache: LRUCache = LRUCache(capacity)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            key = (args, tuple(sorted(kwargs.items())))
            result = cache.get(key, _MISS)
            if result is _MISS:
                result = func(*args, **kwargs)
                cache.put(key, result)
            return result

        wrapper.cache = cache  # type: ignore[attr-defined]
        wrapper.cache_stats = cache.stats  # type: ignore[attr-defined]
        wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
        return wrapper

    return decorate
