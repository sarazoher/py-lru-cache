"""O(1) LRU cache with a function decorator and a caching calculator."""

from .cache import CacheStats, LRUCache
from .calculator import CachingCalculator, Op
from .decorator import lru_cached

__all__ = ["LRUCache", "CacheStats", "lru_cached", "CachingCalculator", "Op"]
__version__ = "2.0.0"
