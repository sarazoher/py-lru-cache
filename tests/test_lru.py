import random
import threading
from collections import OrderedDict

import pytest

from lru import CachingCalculator, LRUCache, Op, lru_cached


# ------------------------------------------------------------------ core behaviour
def test_evicts_least_recently_used():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")                    # "b" is now least recently used
    assert c.put("c", 3) == "b"   # put reports what it evicted
    assert "b" not in c and c.items() == [("c", 3), ("a", 1)]


def test_update_refreshes_recency_without_eviction():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.put("a", 10) is None
    c.put("c", 3)
    assert c.items() == [("c", 3), ("a", 10)]


def test_peek_does_not_change_order():
    c = LRUCache(2)
    c.put("a", 1)
    c.put("b", 2)
    assert c.peek("a") == 1
    c.put("c", 3)
    assert "a" not in c


def test_cached_none_is_distinguishable_from_a_miss():
    c = LRUCache(2)
    c["k"] = None
    assert "k" in c and c["k"] is None
    with pytest.raises(KeyError):
        c["missing"]
    assert c.get("missing", "default") == "default"


@pytest.mark.parametrize("bad", [0, -1, 1.5, "3", None, True])
def test_rejects_invalid_capacity(bad):
    with pytest.raises(ValueError):
        LRUCache(bad)


def test_capacity_one():
    c = LRUCache(1)
    c.put(1, "a")
    c.put(2, "b")
    assert c.items() == [(2, "b")]


def test_pop_delete_clear():
    c = LRUCache(3)
    for k in "abc":
        c[k] = k.upper()
    assert c.pop("b") == "B"
    del c["a"]
    assert c.items() == [("c", "C")]
    with pytest.raises(KeyError):
        c.pop("zzz")
    c.clear()
    assert len(c) == 0 and c.items() == []
    c.put("x", 1)  # still usable after clear
    assert c.items() == [("x", 1)]


def test_stats():
    c = LRUCache(1)
    c.put("a", 1)
    c.get("a")
    c.get("b")
    c.put("b", 2)
    s = c.stats()
    assert (s.hits, s.misses, s.evictions, s.size) == (1, 1, 1, 1)
    assert s.hit_rate == 0.5


def test_equality():
    a, b = LRUCache(2), LRUCache(2)
    for c in (a, b):
        c.put(1, "x")
        c.put(2, "y")
    assert a == b
    b.get(1)  # same contents, different recency order
    assert a != b
    assert a != "not a cache"


def test_matches_reference_model_on_random_operations():
    """Differential test against an OrderedDict-based reference implementation."""
    rng = random.Random(42)
    for capacity in (1, 2, 5, 50):
        cache, ref = LRUCache(capacity), OrderedDict()
        for _ in range(5_000):
            key = rng.randrange(capacity * 3)
            if rng.random() < 0.5:
                expected = ref.get(key)
                if key in ref:
                    ref.move_to_end(key)
                assert cache.get(key) == expected
            else:
                ref[key] = key * 10
                ref.move_to_end(key)
                if len(ref) > capacity:
                    ref.popitem(last=False)
                cache.put(key, key * 10)
            assert cache.items() == list(reversed(ref.items()))


def test_thread_safety():
    c = LRUCache(64)

    def worker(seed):
        rng = random.Random(seed)
        for _ in range(5_000):
            k = rng.randrange(128)
            c.put(k, k) if rng.random() < 0.5 else c.get(k)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    items = c.items()
    assert len(items) == len(c) <= 64
    assert all(k == v for k, v in items)


# ------------------------------------------------------------------ decorator
def test_decorator_memoises_and_evicts():
    calls = []

    @lru_cached(capacity=2)
    def square(x):
        calls.append(x)
        return x * x

    assert [square(2), square(2), square(3), square(4), square(2)] == [4, 4, 9, 16, 4]
    assert calls == [2, 3, 4, 2]  # 2 was evicted by 4 and recomputed
    assert square.cache_stats().hits == 1
    assert square.__name__ == "square"


def test_decorator_keyword_order_does_not_matter():
    @lru_cached()
    def f(a=0, b=0):
        return object()

    assert f(a=1, b=2) is f(b=2, a=1)


# ------------------------------------------------------------------ calculator
def test_calculator_hits_and_misses():
    calc = CachingCalculator(capacity=3)
    assert calc.calculate(4, "mul", 3) == (12, False)
    assert calc.calculate(4, "*", 3) == (12, True)


def test_calculator_commutative_operations_share_entries():
    calc = CachingCalculator()
    calc.calculate(4, Op.ADD, 3)
    assert calc.calculate(3, Op.ADD, 4) == (7, True)
    calc.calculate(10, Op.SUB, 2)
    assert calc.calculate(2, Op.SUB, 10) == (-8, False)


def test_calculator_errors():
    calc = CachingCalculator()
    with pytest.raises(ZeroDivisionError):
        calc.calculate(1, "div", 0)
    assert len(calc.cache) == 0  # errors are not cached
    with pytest.raises(ValueError, match="unknown operator"):
        calc.calculate(2, "pow", 3)
