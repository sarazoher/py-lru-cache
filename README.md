# py-lru-cache

A thread-safe least-recently-used (LRU) cache in pure Python with O(1) `get` and `put`,
a `@lru_cached` decorator, and a small calculator that memoises its results.

Started as an Advanced Python course project with a list-based, O(n) design. Version 2 is
a rewrite with a new data structure, bug fixes, tests and a benchmark.

## How it works

```
dict:          key ──► node
linked list:   HEAD ⇄ [most recent] ⇄ … ⇄ [least recent] ⇄ TAIL
```

A dictionary finds a key's node in O(1). A doubly linked list keeps recency order: a hit
unlinks the node and pushes it to the front (O(1)), and eviction removes the node in front
of the `TAIL` sentinel (O(1)). Sentinel nodes at both ends mean no empty-list special
cases. A re-entrant lock makes every public method safe to call from several threads.

## Usage

```python
from lru import LRUCache, lru_cached, CachingCalculator

cache = LRUCache(capacity=3)
cache["a"] = 1                 # or cache.put("a", 1)
cache.get("a")                 # 1, and "a" becomes most recently used
cache.get("missing", "dflt")   # "dflt"
evicted = cache.put("x", 9)    # returns the evicted key, or None
cache.stats()                  # CacheStats(hits=…, misses=…, evictions=…, size=…, capacity=3)

@lru_cached(capacity=256)
def fib(n): return n if n < 2 else fib(n - 1) + fib(n - 2)

calc = CachingCalculator(capacity=100)
calc.calculate(4, "*", 3)      # (12, False): computed
calc.calculate(3, "*", 4)      # (12, True):  commutative ops share one cache entry
```

Run `python example.py` for a short tour.

## Benchmark

200,000 operations (80% get / 20% put, keys drawn from twice the capacity),
`python benchmarks/bench.py`:

| capacity | LRUCache (this repo) | original list version | `functools.lru_cache` (C) |
|---------:|---------------------:|----------------------:|--------------------------:|
|      100 |              0.075 s |               0.074 s |                   0.015 s |
|    1,000 |              0.076 s |               0.852 s |                   0.017 s |
|   10,000 |              0.074 s |               5.371 s |                   0.023 s |

The linked-list version stays flat as the cache grows, while the original slows down
linearly because `list.remove()` and `list.pop(0)` scan the whole list. The standard
library's C implementation is still about 4x faster; this repo's version adds an explicit
cache object you can inspect, `peek`, `pop`, eviction reporting and per-cache stats.

## What changed from the original

| Problem in v1 | Fix in v2 |
|---|---|
| Recency tracked in a list → O(n) per operation | Hash map + doubly linked list → O(1) |
| `LruCache(size=0).put(...)` crashed with `IndexError` (validation only ran in the setter, not in `__init__`) | Capacity validated in the constructor |
| A cached `None` was indistinguishable from a miss | `get(key, default)` with a sentinel; `__getitem__` raises `KeyError` |
| `Calculator.__eq__` read attributes that don't exist | Removed; equality is defined on the cache (contents + recency order) |
| Unknown operators silently returned `None` and cached it | `Op` enum; unknown operators raise `ValueError` |
| `4+3` and `3+4` were separate cache entries | Commutative operations normalise their key |
| No tests | 21 pytest tests, including a differential test against an `OrderedDict` reference model and a multi-threaded stress test |

## Tests

```bash
pip install pytest
pytest -q
```

## License

MIT
