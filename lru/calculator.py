"""A calculator that memoises results in an LRUCache (the original assignment's use case)."""

from __future__ import annotations

import operator
from enum import Enum
from numbers import Real

from .cache import LRUCache

_MISS = object()


class Op(Enum):
    ADD = ("+", operator.add, True)
    SUB = ("-", operator.sub, False)
    MUL = ("*", operator.mul, True)
    DIV = ("/", operator.truediv, False)

    def __init__(self, symbol, func, commutative):
        self.symbol = symbol
        self.func = func
        self.commutative = commutative

    @classmethod
    def parse(cls, value: "Op | str") -> "Op":
        if isinstance(value, Op):
            return value
        aliases = {"sum": cls.ADD, "add": cls.ADD, "sub": cls.SUB, "mul": cls.MUL, "div": cls.DIV}
        aliases.update({op.symbol: op for op in cls})
        try:
            return aliases[value.lower()]
        except (KeyError, AttributeError):
            raise ValueError(f"unknown operator {value!r}; expected one of {sorted(aliases)}") from None


class CachingCalculator:
    def __init__(self, capacity: int = 128) -> None:
        self.cache: LRUCache[tuple, float] = LRUCache(capacity)

    @staticmethod
    def key(left: Real, op: Op, right: Real) -> tuple:
        # Order operands of commutative operators so 3+4 and 4+3 share one entry.
        if op.commutative and (right, left) < (left, right):
            left, right = right, left
        return (op.name, left, right)

    def calculate(self, left: Real, op: "Op | str", right: Real) -> tuple[float, bool]:
        """Return ``(result, cache_hit)``. Errors such as division by zero are not cached."""
        op = Op.parse(op)
        k = self.key(left, op, right)
        cached = self.cache.get(k, _MISS)
        if cached is not _MISS:
            return cached, True
        if op is Op.DIV and right == 0:
            raise ZeroDivisionError(f"{left} / 0")
        result = op.func(left, right)
        self.cache.put(k, result)
        return result, False
