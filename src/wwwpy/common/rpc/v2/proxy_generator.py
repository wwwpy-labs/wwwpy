import ast
from typing import Type

from wwwpy.common.rpc.v2.dispatcher import Dispatcher


def generate(source: str, dispatch_builder_provider: Type[Dispatcher]) -> str:
    """This function is used to parse a source code and generate a new source code that:
- Instantiates a DispatcherBuilder, one for the top level module and one for each class
- calls definition_complete at the end of each class and the module
- calls new_dispatcher at the end of the module and in the __init__ of each class
- keeps the definition of the functions/methods with type hints
- removes the implementation of the functions and replaces it with a forwarding call to its contextual
dispatcher (being it the module or a class dispatcher)

See the protocol DispatcherBuilder
"""
    tree: ast.Module = ast.parse(source)
    module = dispatch_builder_provider.__module__
    qualified_name = dispatch_builder_provider.__qualname__

    lines = [
        f'from {module} import {qualified_name}',
        f'dispatcher = {qualified_name}()',
        ''
    ]
    used_annotations = set()
    for b in tree.body:
        if isinstance(b, ast.FunctionDef):
            b.body = []  # keep only the signature
            func_def = ast.unparse(b)
            lines.append(func_def)
            args_list = []
            for ar in b.args.args:
                used_annotations.add(ar.annotation)
                args_list.append(f'({ar.arg}, {ast.unparse(ar.annotation)})')
            args = '[' + ', '.join(args_list) + ']'
            lines.append(f'    return dispatcher.dispatch_module_function("{b.name}", {args})')

        elif isinstance(b, (ast.ImportFrom, ast.Import)):
            lines.append(b)

    for idx in range(len(lines)):
        line = lines[idx]
        if isinstance(line, ast.stmt):
            line = ast.unparse(line)
        lines[idx] = line

    lines.append('dispatcher.definition_complete(locals(), "module")')

    body = '\n'.join(lines)
    return body
