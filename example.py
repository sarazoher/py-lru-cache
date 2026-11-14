"""Quick tour: python example.py"""

from lru import CachingCalculator, LRUCache, lru_cached

cache = LRUCache(capacity=3)
for key in "abc":
    cache[key] = key.upper()
cache.get("a")                      # touch "a" so "b" becomes least recently used
print("evicted:", cache.put("d", "D"))
print(cache)
print(cache.stats())

calc = CachingCalculator(capacity=3)
print(calc.calculate(4, "*", 3))    # (12, False)  computed
print(calc.calculate(3, "*", 4))    # (12, True)   commutative -> same cache entry


@lru_cached(capacity=256)
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)


print("fib(200) =", fib(200))
print(fib.cache_stats())
