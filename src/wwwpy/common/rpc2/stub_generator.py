from __future__ import annotations

import types
from types import SimpleNamespace

from wwwpy.common.designer import code_info
from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.transport import Transport


class Skeleton:
    def invoke(self, module_name: str, name: str, *args):
        """name can be
        - a function name
        - a method name in the form of 'class_name.method'

        In the case this is a method invocation the first element of args can be None or any value
        that can be used by the implementation to link a Called object to the Caller object
        """


class JsonStub:
    def __init__(self, dispatcher: Transport):
        self.dispatcher = dispatcher


class Stub:
    """
    See naming conventions at https://en.wikipedia.org/wiki/Distributed_object_communication

    This is class is placed inside the generated source code, so it MUST be available on the Caller side.
    It will be instantiated when the module is loaded on the Caller side and not at generation time.

    It requires the __module__ and __qualname__ attributes. because they will be used to generate the import statement
    and the instantiation in the generated source code; classes and functions have these attributes.
    """
    __module__: str
    __qualname__: str

    namespace: any
    """This is the namespace that will be used to forward the function/method calls to the Stub implementation    
    """

    def setup_functions(self, *functions: types.FunctionType) -> None:
        """This must setup the namespace for the functions"""

    def setup_classes(self, *classes: type) -> None:
        """This must setup the namespace for the classes"""


class StubGenerator:
    """Generates a stub source code from the given source code.
The goals are:
- forward the function/method calls to the stub
- generate the module_init call at the end of the generated source code
- preserve the type hints and default parameters of the functions/methods
- preserve the import and importFrom statements so the type hints are available
    """

    def parse(self, source: str) -> code_info.Info:
        return code_info.info(source)

    def generate(self, source: str, stub_type: type[Stub], stub_args: str = '') -> str:
        """Parses the given source code and generates a new source code that:
        - calls module_init at the end the generated source code
        - calls dispatch_sync/dispatch_async for each function/method
        - removes the implementation of the functions and replaces it with a forwarding call to the stub

        Inclusion/Exclusion
        - MUST generate also a class __init__ method
        - MUST NOT generate entities (function/method/class) that starts with '_'
        """


def generate_stub(source: str, stub_type: type[Stub], stub_args: str = '') -> str:
    # return StubGenerator().generate(source, stub_type, stub_args)
    return ''


class DefaultStub(Stub):

    def __init__(self, transport: Transport, enc_dec: EncoderDecoder):
        self.namespace = SimpleNamespace()
        self.encoder = enc_dec.encoder
        self.decoder = enc_dec.decoder
        self.transport = transport


# language=python
"""
from some_module import SomeThing # noqa
_stub = Stub(__name__, stub_args) # noqa

def add(a: int, b: int) -> int:
    return _stub.namespace.add(a, b)

async def sub(a: int, b: int) -> SomeThing:
    return await _stub.namespace.sub(a, b)

class Class1:
    
    def __init__(self):
        return _stub.namespace.Class1.__init__(self)
    
    def add(self, c: int) -> int:
        return _stub.namespace.Class1.add(self, c)

class Class2:
        
    async def sub(self, c: int) -> int:
        return await _stub.namespace.Class1.sub(self, c)
    
            
_stub.setup_functions(add, sub)
_stub.setup_classes(Class1, Class2)

"""
