from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FunctionDef:
    name: str
    annotations: list[type]
    return_annotation: type


@dataclass(frozen=True)
class Definition:
    target: str
    functions: dict[str, FunctionDef]


class Dispatcher(Protocol):
    """
    This Caller/Callee convention this is the Caller.
    https://en.wikipedia.org/wiki/Calling_convention

    This is used by the proxy_generator to be used inside the generated source code.
    The proxy_generator will instantiate a Dispatcher for the module and one for each class.

    It requires the __module__ and __qualname__ attributes. because they will be they will be imported
    in the generated source code.

    For example, classes and functions have these attributes.
    """
    __module__: str
    __qualname__: str

    def definition_complete(self, definition: Definition) -> None:
        """The proxy_generator will call this method when the top level module
    is parsed and also at the end of each class definition. This allows the implementation to
    inspect the functions and their type hints through the locals() dictionary."""
        ...

    def dispatch_sync(self, function_name: str, *args) -> any:
        """The proxy_generator will call this method to dispatch a function call to the implementation."""
        ...

    async def dispatch_async(self, function_name: str, *args) -> any:
        """The proxy_generator will call this method to dispatch a function call to the implementation."""
        ...
