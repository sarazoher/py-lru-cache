"""An O(1) least-recently-used cache: a hash map for lookup plus a doubly linked list
for recency order.

    dict:   key -> node
    list:   head <-> [most recent] <-> ... <-> [least recent] <-> tail

``get`` and ``put`` move a node to the front in O(1); eviction removes the node just
before the tail sentinel in O(1). Sentinel nodes remove all the "is this the first /
last element?" special cases.
"""

from __future__ import annotations

import threading
from collections.abc import Hashable, Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

_MISSING = object()


class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev: _Node | None = None
        self.next: _Node | None = None


@dataclass(frozen=True)
class CacheStats:
    hits: int
    misses: int
    evictions: int
    size: int
    capacity: int

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total else 0.0


class LRUCache(Generic[K, V]):
    """Fixed-capacity mapping that evicts the least recently used entry when full.

    Thread-safe: every public method holds an internal lock.
    """

    def __init__(self, capacity: int) -> None:
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity <= 0:
            raise ValueError(f"capacity must be a positive integer, got {capacity!r}")
        self._capacity = capacity
        self._map: dict[K, _Node] = {}
        self._head = _Node()  # sentinel before the most recently used entry
        self._tail = _Node()  # sentinel after the least recently used entry
        self._head.next, self._tail.prev = self._tail, self._head
        self._lock = threading.RLock()
        self._hits = self._misses = self._evictions = 0

    # ---------------------------------------------------------------- linked-list helpers
    def _unlink(self, node: _Node) -> None:
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node: _Node) -> None:
        node.prev, node.next = self._head, self._head.next
        self._head.next.prev = node
        self._head.next = node

    # ---------------------------------------------------------------- public API
    @property
    def capacity(self) -> int:
        return self._capacity

    def get(self, key: K, default=None):
        """Return the value for ``key`` and mark it most recently used, else ``default``."""
        with self._lock:
            node = self._map.get(key)
            if node is None:
                self._misses += 1
                return default
            self._hits += 1
            self._unlink(node)
            self._push_front(node)
            return node.value

    def put(self, key: K, value: V) -> K | None:
        """Insert or update ``key``. Returns the evicted key, if an eviction happened."""
        with self._lock:
            node = self._map.get(key)
            if node is not None:
                node.value = value
                self._unlink(node)
                self._push_front(node)
                return None

            evicted = None
            if len(self._map) >= self._capacity:
                lru = self._tail.prev
                self._unlink(lru)
                del self._map[lru.key]
                self._evictions += 1
                evicted = lru.key

            node = _Node(key, value)
            self._map[key] = node
            self._push_front(node)
            return evicted

    def peek(self, key: K, default=None):
        """Like ``get`` but does not change recency or statistics."""
        with self._lock:
            node = self._map.get(key)
            return default if node is None else node.value

    def pop(self, key: K, default=_MISSING):
        with self._lock:
            node = self._map.pop(key, None)
            if node is None:
                if default is _MISSING:
                    raise KeyError(key)
                return default
            self._unlink(node)
            return node.value

    def clear(self) -> None:
        with self._lock:
            self._map.clear()
            self._head.next, self._tail.prev = self._tail, self._head

    def stats(self) -> CacheStats:
        with self._lock:
            return CacheStats(self._hits, self._misses, self._evictions,
                              len(self._map), self._capacity)

    def items(self) -> list[tuple[K, V]]:
        """Snapshot of entries, most recently used first."""
        with self._lock:
            out, node = [], self._head.next
            while node is not self._tail:
                out.append((node.key, node.value))
                node = node.next
            return out

    # ---------------------------------------------------------------- mapping protocol
    def __getitem__(self, key: K) -> V:
        value = self.get(key, _MISSING)
        if value is _MISSING:
            raise KeyError(key)
        return value

    def __setitem__(self, key: K, value: V) -> None:
        self.put(key, value)

    def __delitem__(self, key: K) -> None:
        self.pop(key)

    def __contains__(self, key: object) -> bool:
        return key in self._map

    def __len__(self) -> int:
        return len(self._map)

    def __iter__(self) -> Iterator[K]:
        return iter([k for k, _ in self.items()])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LRUCache):
            return NotImplemented
        return self._capacity == other._capacity and self.items() == other.items()

    __hash__ = None  # mutable container

    def __repr__(self) -> str:
        body = ", ".join(f"{k!r}: {v!r}" for k, v in self.items())
        return f"LRUCache(capacity={self._capacity}, {{{body}}})"
