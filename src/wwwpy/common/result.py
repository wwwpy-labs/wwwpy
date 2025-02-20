from __future__ import annotations
from typing import Generic, TypeVar, Union

_S = TypeVar('_S')
"""Success type variable"""
_F = TypeVar('_F')
"""Failure type variable"""


class Result(Generic[_S, _F]):
    def __init__(self, value: Union[_S, _F], is_success: bool):
        self._value = value
        self._is_success = is_success

    @staticmethod
    def success(value: _S) -> 'Success[_S, _F]':
        return Success(value)

    @staticmethod
    def failure(error: _F) -> 'Failure[_S, _F]':
        return Failure(error)

    @property
    def is_success(self) -> bool:
        return self._is_success

    @property
    def is_failure(self) -> bool:
        return not self._is_success

    def get_or_null(self) -> _S | None:
        return self._value if self.is_success else None

    def error_or_null(self) -> _F | None:
        return self._value if self.is_failure else None

    def get_or_throw(self) -> _S:
        if self.is_success:
            return self._value

        exc = self._value
        if not isinstance(self._value, BaseException):
            exc = Exception(self._value)
        raise exc

    def __repr__(self) -> str:
        return f"Success({self._value})" if self.is_success else f"Failure({self._value})"


class Success(Result[_S, _F]):
    def __init__(self, value: _S):
        super().__init__(value, True)


class Failure(Result[_S, _F]):
    def __init__(self, error: _F):
        super().__init__(error, False)
