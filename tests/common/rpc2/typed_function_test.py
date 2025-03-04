from __future__ import annotations

from wwwpy.common.rpc2.typed_function import get_typed_function, TypedFunction


class Car: ...


def mock_fun(a: int, b: Car) -> float: ...


def test_get():
    target = get_typed_function(mock_fun)

    assert target == TypedFunction(__name__, 'mock_fun', [int, Car], float)
