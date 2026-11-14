"""Compare the O(1) LRUCache with the original O(n) list version and functools.lru_cache.

Workload: 200k operations, 80% get / 20% put, keys drawn from a range 2x the capacity.

    python benchmarks/bench.py
"""

import functools
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lru import LRUCache  # noqa: E402
from naive_lru import NaiveLRU  # noqa: E402

N_OPS = 200_000


def workload(capacity, seed=0):
    rng = random.Random(seed)
    return [(rng.random() < 0.8, rng.randrange(capacity * 2)) for _ in range(N_OPS)]


def run(cache, ops):
    start = time.perf_counter()
    for is_get, key in ops:
        if is_get:
            cache.get(key)
        else:
            cache.put(key, key)
    return time.perf_counter() - start


def run_functools(capacity, ops):
    @functools.lru_cache(maxsize=capacity)
    def f(key):
        return key
    start = time.perf_counter()
    for _, key in ops:
        f(key)
    return time.perf_counter() - start


def main():
    print(f"{'capacity':>9} | {'LRUCache (O(1))':>16} | {'original (O(n))':>16} | {'functools (C)':>14}")
    print("-" * 66)
    for capacity in (100, 1_000, 10_000):
        ops = workload(capacity)
        fast = run(LRUCache(capacity), ops)
        naive = run(NaiveLRU(capacity), ops)
        ft = run_functools(capacity, ops)
        print(f"{capacity:>9,} | {fast:>14.3f} s | {naive:>14.3f} s | {ft:>12.3f} s")


if __name__ == "__main__":
    main()
