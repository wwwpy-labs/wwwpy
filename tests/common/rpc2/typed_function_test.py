from __future__ import annotations

from wwwpy.common.rpc2.typed_function import get_typed_function, TypedFunction


class Car: ...


def test_sync():
    def mock_sync(a: int, b: Car) -> float: ...

    target = get_typed_function(mock_sync)

    assert target == TypedFunction(__name__, 'mock_sync', [int, Car], float, False)


def test_async():
    async def mock_async(a: int, b: Car) -> float: ...

    target = get_typed_function(mock_async)

    assert target == TypedFunction(__name__, 'mock_async', [int, Car], float, True)
