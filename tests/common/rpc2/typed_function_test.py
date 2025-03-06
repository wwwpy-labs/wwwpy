from __future__ import annotations

import dataclasses

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


def test_none_type():
    def none_explicit(a: int) -> None: ...

    def none_implicit(a: int): ...

    expected = TypedFunction(__name__, 'none_explicit', [int], type(None), False)
    assert get_typed_function(none_explicit) == dataclasses.replace(expected, func_name='none_explicit')
    assert get_typed_function(none_implicit) == dataclasses.replace(expected, func_name='none_implicit')
