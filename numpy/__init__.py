"""Lightweight numpy compatibility layer for validation tests."""

from __future__ import annotations

import builtins
import math
import random as _random
from typing import Any, Iterator, List, Sequence, Union

Number = Union[int, float]


def _to_native(value: Any) -> Any:
    if isinstance(value, ndarray):
        return value.tolist()
    return value


def _deep_copy(value: Any) -> Any:
    if isinstance(value, list):
        return [_deep_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_deep_copy(item) for item in value)
    if isinstance(value, ndarray):
        return value.tolist()
    return value


class ndarray:
    """Minimal ndarray wrapper backed by nested Python lists."""

    def __init__(self, data: Any):
        self._data = _deep_copy(list(data)) if isinstance(data, (list, tuple, ndarray)) else data

    def __iter__(self) -> Iterator[Any]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, key):
        if isinstance(key, tuple):
            rows, cols = key
            selected_rows = self._select(self._data, rows)
            if isinstance(selected_rows, list):
                if isinstance(cols, slice):
                    return ndarray([self._select(row, cols) for row in selected_rows])
                return ndarray([row[cols] for row in selected_rows])
            if isinstance(cols, slice):
                return ndarray(selected_rows[cols])
            return selected_rows[cols]
        result = self._select(self._data, key)
        if isinstance(result, list):
            return ndarray(result)
        return result

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            rows, cols = key
            row_indices = self._indices(rows, len(self._data))
            for row_idx in row_indices:
                if isinstance(cols, slice):
                    col_indices = self._indices(cols, len(self._data[row_idx]))
                    for offset, col_idx in enumerate(col_indices):
                        self._data[row_idx][col_idx] = value[offset] if isinstance(value, (list, tuple)) else value
                else:
                    replacement = value[row_idx] if isinstance(value, (list, tuple)) else value
                    self._data[row_idx][cols] = replacement
            return
        self._data[key] = value

    def tolist(self) -> List[Any]:
        return _deep_copy(self._data)

    def copy(self) -> "ndarray":
        return ndarray(self._data)

    def __add__(self, other):
        return _elementwise(self, other, lambda a, b: a + b)

    def __radd__(self, other):
        return _elementwise(other, self, lambda a, b: a + b)

    def __sub__(self, other):
        return _elementwise(self, other, lambda a, b: a - b)

    def __rsub__(self, other):
        return _elementwise(other, self, lambda a, b: a - b)

    def __mul__(self, other):
        return _elementwise(self, other, lambda a, b: a * b)

    def __rmul__(self, other):
        return _elementwise(other, self, lambda a, b: a * b)

    def __truediv__(self, other):
        return _elementwise(self, other, lambda a, b: a / b)

    def __rtruediv__(self, other):
        return _elementwise(other, self, lambda a, b: a / b)

    @staticmethod
    def _select(data: Any, index):
        if isinstance(index, slice):
            return data[index]
        return data[index]

    @staticmethod
    def _indices(index, length: int) -> List[int]:
        if isinstance(index, slice):
            return list(range(*index.indices(length)))
        return [index]


ndarray.__name__ = "ndarray"


def _elementwise(a: Any, b: Any, op):
    left = _to_native(a)
    right = _to_native(b)

    if isinstance(left, list):
        if isinstance(right, list):
            return ndarray([op(x, y) for x, y in zip(left, right)])
        return ndarray([op(x, right) for x in left])

    if isinstance(right, list):
        return ndarray([op(left, y) for y in right])

    return op(left, right)


def array(data: Any) -> ndarray:
    if isinstance(data, ndarray):
        return data.copy()
    return ndarray(data)


def asarray(data: Any) -> ndarray:
    return array(data)


def mean(values: Any) -> float:
    seq = _flatten(values)
    return sum(seq) / len(seq) if seq else 0.0


def var(values: Any) -> float:
    seq = _flatten(values)
    if not seq:
        return 0.0
    m = mean(seq)
    return sum((v - m) ** 2 for v in seq) / len(seq)


def std(values: Any) -> float:
    return math.sqrt(var(values))


def diff(values: Any) -> ndarray:
    seq = _flatten(values)
    return ndarray([seq[i + 1] - seq[i] for i in range(len(seq) - 1)])


def sqrt(value: Union[Number, ndarray]) -> Union[float, ndarray]:
    if isinstance(value, ndarray):
        return ndarray([math.sqrt(v) for v in value])
    return math.sqrt(value)


def tanh(value: Union[Number, ndarray]) -> Union[float, ndarray]:
    if isinstance(value, ndarray):
        return ndarray([math.tanh(v) for v in value])
    return math.tanh(value)


def sin(value: Union[Number, ndarray]) -> Union[float, ndarray]:
    if isinstance(value, ndarray):
        return ndarray([math.sin(v) for v in value])
    return math.sin(value)


def exp(value: Union[Number, ndarray]) -> Union[float, ndarray]:
    if isinstance(value, ndarray):
        return ndarray([math.exp(v) for v in value])
    return math.exp(value)


def cumsum(values: Any) -> ndarray:
    seq = _flatten(values)
    total = 0.0
    result = []
    for val in seq:
        total += val
        result.append(total)
    return ndarray(result)


class _Maximum:
    def accumulate(self, values: Any) -> ndarray:
        seq = _flatten(values)
        result = []
        current = None
        for val in seq:
            current = val if current is None or val > current else current
            result.append(current)
        return ndarray(result)


maximum = _Maximum()


def max(values: Any) -> Number:
    return builtins.max(_flatten(values))


def min(values: Any) -> Number:
    return builtins.min(_flatten(values))


def zeros(length: int) -> ndarray:
    return ndarray([0.0 for _ in range(length)])


def ones(length: int) -> ndarray:
    return ndarray([1.0 for _ in range(length)])


def ones_like(values: Any) -> ndarray:
    seq = _flatten(values)
    return ndarray([1.0 for _ in seq])


def linspace(start: float, stop: float, num: int) -> ndarray:
    if num == 1:
        return ndarray([start])
    step = (stop - start) / (num - 1)
    return ndarray([start + step * i for i in range(num)])


def abs(values: Any) -> Union[Number, ndarray]:
    if isinstance(values, ndarray):
        return ndarray([builtins.abs(v) for v in values])
    return builtins.abs(values)


def array_equal(a: Any, b: Any) -> bool:
    return _flatten(a) == _flatten(b)


pi = math.pi


class _RandomModule:
    def normal(self, loc: float, scale: float, size: int | None = None):
        if size is None:
            return _random.gauss(loc, scale)
        return ndarray([_random.gauss(loc, scale) for _ in range(size)])

    def uniform(self, low: float, high: float, size: int | None = None):
        if size is None:
            return _random.uniform(low, high)
        return ndarray([_random.uniform(low, high) for _ in range(size)])

    def randn(self, size: int | None = None):
        if size is None:
            return _random.gauss(0, 1)
        return ndarray([_random.gauss(0, 1) for _ in range(size)])

    def seed(self, value: int) -> None:
        _random.seed(value)


random = _RandomModule()


def _flatten(values: Any) -> List[float]:
    native = _to_native(values)
    if isinstance(native, list):
        flattened: List[float] = []
        for item in native:
            if isinstance(item, list):
                flattened.extend(float(x) for x in item)
            else:
                flattened.append(float(item))
        return flattened
    return [float(native)]


__all__ = [
    "array",
    "asarray",
    "ndarray",
    "mean",
    "var",
    "std",
    "diff",
    "sqrt",
    "tanh",
    "sin",
    "exp",
    "cumsum",
    "maximum",
    "max",
    "min",
    "zeros",
    "ones",
    "ones_like",
    "linspace",
    "abs",
    "array_equal",
    "pi",
    "random",
]
