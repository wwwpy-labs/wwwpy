from dataclasses import dataclass
from typing import Protocol
import types


@dataclass(frozen=True)
class FunctionDef:
    name: str
    annotations: list[type]
    return_annotation: type = None
    instance: types.FunctionType = None


@dataclass(frozen=True)
class Definition:
    target: str
    functions: dict[str, FunctionDef]


class Dispatcher(Protocol):
    """This protocol is used by the proxy_generator to build a Dispatcher.
    The proxy_generator will instantiate a DispatcherBuilder for each module and class.

    A protocol that also requires the __module__ and __qualname__ attributes.
For example, classes and functions have these attributes.
    """
    __module__: str
    __qualname__: str

    def definition_complete(self, locals_, target: str, definition: Definition) -> None:
        """The proxy_generator will call this method when the top level module
    is parsed and also at the end of each class definition. This allows the implementation to
    inspect the functions and their type hints through the locals() dictionary."""
        ...

    def dispatch_sync(self, function_name: str, *args) -> any:
        """The proxy_generator will call this method to dispatch a function call to the implementation."""
        ...

    def dispatch_async(self, function_name: str, *args) -> any:
        """The proxy_generator will call this method to dispatch a function call to the implementation."""
        ...
