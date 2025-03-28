from __future__ import annotations

import ast
import importlib.util
from ast import Module, FunctionDef, ClassDef
from typing import NamedTuple, List


class Function(NamedTuple):
    name: str
    signature: str
    is_coroutine_function: bool
    parameters: List[Parameters]


class Parameters(NamedTuple):
    name: str
    annotation: str


class FuncMeta:
    """It contains only the information about the functions of a module.
    It does not have the actual functions.
    """

    def __init__(self, name: str, functions: List[Function]):
        self.name = name

        self.functions: List[Function] = functions
        self._funcs = {f.name: f for f in self.functions}

    def __getitem__(self, name) -> Function:
        return self._funcs.get(name, None)


def from_package_name(package_name: str) -> FuncMeta | None:
    """it returns a FuncRegistry object from the given package name. If the package is not found, it returns None.
    The package will not be loaded it will be parsed with ast module.
    """
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return None

    source_code = spec.loader.get_source(package_name)
    functions = function_definitions(source_code)
    return FuncMeta(package_name, functions)


def function_definitions(source_code) -> List[Function]:
    tree = ast.parse(source_code)
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_name = node.name
            args = []
            parameters = []
            for arg in node.args.args:
                arg_name = arg.arg
                arg_annotation = ast.get_source_segment(source_code, arg.annotation) if arg.annotation else None
                args.append(f"{arg_name}: {arg_annotation}" if arg_annotation else arg_name)
                parameters.append(Parameters(arg_name, arg_annotation))

            returns = ast.get_source_segment(source_code, node.returns) if node.returns else None
            signature = '(' + ', '.join(args) + ')' + (f' -> {returns}' if returns else '')
            f = Function(function_name, signature, isinstance(node, ast.AsyncFunctionDef), parameters)
            functions.append(f)

    return functions


def source_to_proxy(module_name: str, source: str) -> str:
    tree: Module = ast.parse(source)
    content = ''
    # todo OptionalCoroutine
    # add detecting unsupported structure (e.g, nested class, AsyncFunctionDef, functions with results), log a warning message

    for b in tree.body:
        if isinstance(b, ClassDef):
            content += f'class {b.name}:\n' \
                       '    def __init__(self, send_endpoint):\n' \
                       '        self.send_endpoint = send_endpoint\n'

            for f in b.body:
                if isinstance(f, FunctionDef):
                    fqn = b.name + '.' + f.name
                    if len(f.args.args) > 1:  # beyond self
                        args = ', ' + ', '.join([a.arg for a in f.args.args[1:]])
                    else:
                        args = ''
                    content += f'    def {f.name}(self{args}):\n' \
                               f'       self.send_endpoint.dispatch("{module_name}", "{fqn}"{args})\n'

    return content
