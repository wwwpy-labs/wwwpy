import ast
from typing import Protocol, Type

from wwwpy.common.rpc.v2.dispatcher import TargetType, Dispatcher


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
    functions = []
    for b in tree.body:
        if isinstance(b, ast.FunctionDef):
            # Reconstruct parameters with type hints
            params = []
            for arg in b.args.args:
                if arg.annotation is not None:
                    params.append(f"{arg.arg}: {ast.unparse(arg.annotation)}")
                else:
                    params.append(arg.arg)
            params_str = ", ".join(params)
            # Reconstruct return annotation if exists
            ret_hint = f" -> {ast.unparse(b.returns)}" if b.returns is not None else ""
            functions.append(f'''
def {b.name}({params_str}){ret_hint}:
    return dispatcher.dispatch_module_function("{b.name}")
''')
    module = dispatch_builder_provider.__module__
    qualified_name = dispatch_builder_provider.__qualname__
    functions_str = "\n".join(functions)
    result = f"""
from {TargetType.__module__} import {TargetType.__name__}
from {module} import {qualified_name}
dispatcher = {qualified_name}()

{functions_str}

dispatcher.definition_complete(locals(), TargetType.module)
    """
    return result