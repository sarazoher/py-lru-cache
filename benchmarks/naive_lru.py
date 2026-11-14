"""The original list-based implementation, kept only for the benchmark.

Recency is tracked in a Python list, so every get/put calls list.remove(key) and
eviction calls list.pop(0): both O(n) in the number of cached keys.
"""


class NaiveLRU:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}
        self.order = []

    def _touch(self, key):
        if key in self.order:
            self.order.remove(key)
        self.order.append(key)

    def get(self, key, default=None):
        if key not in self.cache:
            return default
        self._touch(key)
        return self.cache[key]

    def put(self, key, value):
        if key not in self.cache and len(self.cache) >= self.capacity:
            del self.cache[self.order.pop(0)]
        self._touch(key)
        self.cache[key] = value
