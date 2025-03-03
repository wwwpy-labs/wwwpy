from __future__ import annotations

import ast
import types
from types import SimpleNamespace
from typing import Optional

from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.transport import Transport


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


_annotations_type = set[ast.Name]


# def caller_proxy_generate(source: str, dispatcher_callable: Type[Dispatcher], dispatcher_args: str = '') -> str:
# def generate_stub(source: str, stub_type: type[Stub], stub_args: str = '') -> str:
def generate_stub(source: str, stub_type: type[Stub], stub_args: str = '') -> str:
    """Generates a stub source code from the given source code.
The goals are:
- forward the function/method calls to the stub
- preserve the type hints and default parameters of the functions/methods
- preserve the import and importFrom statements so the type hints are available
- removes the implementation of the functions and replaces it with a forwarding call to the stub

Inclusion/Exclusion
- MUST NOT generate entities (function/method/class) that starts with '_'
    """

    tree: ast.Module = ast.parse(source)
    module = stub_type.__module__
    qualified_name = stub_type.__qualname__
    lines = [
        f'from {module} import {qualified_name}',
        f'dispatcher = {qualified_name}({stub_args})',
        ''
    ]
    used_annotations: _annotations_type = set()
    function_names = []
    class_names = []
    for b in tree.body:
        if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and not b.name.startswith('_'):
            _add_function_or_method(lines, b, used_annotations)
            function_names.append(b.name)
        elif isinstance(b, (ast.ImportFrom, ast.Import)):
            lines.append(b)
        elif isinstance(b, ast.ClassDef) and not b.name.startswith('_'):
            class_names.append(b.name)
            class_body = b.body
            b.body = []
            class_def = ast.unparse(b)
            lines.append(class_def)
            indent = '    '
            method_count = 0
            for m in class_body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith('_'):
                    m.body = []  # keep only the signature
                    func_def = ast.unparse(m)
                    lines.append(indent + func_def)
                    args_list = []
                    anno_list = []
                    for ar in m.args.args:
                        pass
                        # used_annotations.add(ar.annotation)
                        # args_list.append(f'{ar.arg}')
                        # anno_list.append(ast.unparse(ar.annotation))
                    args = ', '.join(args_list)
                    # if m.returns:
                    #     used_annotations.add(m.returns)

                    is_async = isinstance(m, ast.AsyncFunctionDef)
                    async_spec = 'await ' if is_async else ''
                    lines.append(indent + f'    return {async_spec}dispatcher.namespace.{b.name}.{m.name}({args})')
                    lines.append('')  # empty line after each function
                    method_count += 1
            if method_count == 0:
                lines.append(indent + 'pass')

    for idx in range(len(lines)):
        line = lines[idx]
        if isinstance(line, ast.Import):
            lines[idx] = ast.unparse(line) if _is_import_used(line, used_annotations) else ''
        elif isinstance(line, ast.ImportFrom):
            lines[idx] = ast.unparse(line) if _is_import_from_used(line, used_annotations) else ''

    # setup_functions call
    lines.append(f'dispatcher.setup_functions({", ".join(function_names)})')
    # setup_classes call
    lines.append(f'dispatcher.setup_classes({", ".join(class_names)})')

    body = '\n'.join(lines)
    return body


def _add_function_or_method(lines, b, used_annotations):
    b.body = []  # keep only the signature
    func_def = ast.unparse(b)
    lines.append(func_def)
    args_list = []
    anno_list = []
    for ar in b.args.args:
        used_annotations.add(ar.annotation)
        args_list.append(f'{ar.arg}')
        anno_list.append(ast.unparse(ar.annotation))
    args = ', '.join(args_list)
    if b.returns:
        used_annotations.add(b.returns)
    is_async = isinstance(b, ast.AsyncFunctionDef)
    async_spec = 'await ' if is_async else ''
    lines.append(f'    return {async_spec}dispatcher.namespace.{b.name}({args})')
    lines.append('')  # empty line after each function


def _is_import_used(node: ast.Import, used_annotations: _annotations_type) -> bool:
    for alias in node.names:
        candidate = alias.asname if alias.asname is not None else alias.name
        for ann in used_annotations:
            if _annotation_uses_candidate(ann, candidate):
                return True
    return False


def _is_import_from_used(node: ast.ImportFrom, used_annotations: _annotations_type) -> bool:
    for alias in node.names:
        candidate = alias.asname if alias.asname is not None else alias.name
        for ann in used_annotations:
            if _annotation_uses_candidate(ann, candidate):
                return True
    return False


def _annotation_uses_candidate(node: ast.AST, candidate: str) -> bool:
    full_name = _get_full_name(node)
    if full_name is not None:
        if full_name == candidate or full_name.startswith(candidate + '.'):
            return True
    for child in ast.iter_child_nodes(node):
        if _annotation_uses_candidate(child, candidate):
            return True
    return False


def _get_full_name(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        base = _get_full_name(node.value)
        if base is not None:
            return base + '.' + node.attr
    return None


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
