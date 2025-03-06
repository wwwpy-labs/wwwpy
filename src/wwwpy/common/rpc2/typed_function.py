from __future__ import annotations

import inspect
import types
import typing
from dataclasses import dataclass


@dataclass
class TypedFunction:
    module_name: str
    func_name: str
    args_types: list[type]
    return_type: type  # this MUST be present also for void functions
    is_coroutine: bool

    def __post_init__(self):
        if self.return_type is None:
            raise Exception(f'Return type missing for function {self.func_name}')


def get_typed_function(function: types.FunctionType) -> TypedFunction:
    type_hints = typing.get_type_hints(function)  # to be used if the below code do not resolve types

    signature = inspect.signature(function)
    args_types = []
    for name, param in signature.parameters.items():
        annotation = type_hints.get(name, None)
        if annotation is None:
            raise Exception(
                f'There is no support for not annotated arguments. Annotation missing for parameter {name} in function {function.__name__}')
        args_types.append(annotation)

    return_annotation = type_hints.get('return', type(None))
    return TypedFunction(
        function.__module__,
        function.__name__,
        args_types,
        return_annotation,
        inspect.iscoroutinefunction(function)
    )
