from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar, Union

_S = TypeVar('_S')
"""Success type variable"""
_F = TypeVar('_F')
"""Failure type variable"""


@dataclass(frozen=True)
class Result(Generic[_S, _F]):
    _value: Union[_S, _F]
    _is_success: bool

    @staticmethod
    def success(value: _S) -> Success[_S, _F]:
        return Success(value)

    @staticmethod
    def failure(error: _F) -> Failure[_S, _F]:
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


def main():
    from typing import get_origin, get_args

    result_type = Result[int, str]
    print("Origin:", get_origin(result_type))  # Should print: <class '__main__.Result'>
    print("Args:", get_args(result_type))  # Should print: (<class 'int'>, <class 'str'>)

    success = Result.success(42)
    print("Instance type args:", get_args(success.__orig_class__))  # Extract generics from an instance


if __name__ == '__main__':
    main()
