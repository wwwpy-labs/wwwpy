import ast
from typing import Type, Optional

from wwwpy.common.rpc.v2.dispatcher import Dispatcher, Definition, FunctionDef

_annotations_type = set[ast.Name]


def caller_proxy_generate(source: str, dispatcher_callable: Type[Dispatcher], dispatcher_args: str = '') -> str:
    """
In the caller/callee this is a caller proxy generator.

    This function is used to parse a source code and generate a new source code that:
- calls definition_complete at the end of each class and the module
- handles the definition of the functions/methods with type hints
- removes the implementation of the functions and replaces it with a forwarding call to its contextual
dispatcher (being it the module or a class dispatcher)

See the protocol DispatcherBuilder
"""
    tree: ast.Module = ast.parse(source)
    module = dispatcher_callable.__module__
    qualified_name = dispatcher_callable.__qualname__
    lines = [
        f'from {module} import {qualified_name}',
        f'dispatcher = {qualified_name}({dispatcher_args})',
        ''
    ]
    used_annotations: _annotations_type = set()
    functions = {}
    for b in tree.body:
        if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and not b.name.startswith('_'):
            b.body = []  # keep only the signature
            func_def = ast.unparse(b)
            lines.append(func_def)
            args_list = []
            anno_list = []
            for ar in b.args.args:
                used_annotations.add(ar.annotation)
                args_list.append(f'{ar.arg}')
                anno_list.append(ast.unparse(ar.annotation))
            args = f'"{b.name}", ' + ', '.join(args_list)
            return_type = 'None'
            if b.returns:
                return_type = ast.unparse(b.returns)
                used_annotations.add(b.returns)
            functions[b.name] = f'FunctionDef("{b.name}", [{", ".join(anno_list)}], {return_type})'
            if isinstance(b, ast.AsyncFunctionDef):
                lines.append(f'    return await dispatcher.dispatch_async({args})')
            else:
                lines.append(f'    return dispatcher.dispatch_sync({args})')
            lines.append('')  # empty line after each function
        elif isinstance(b, (ast.ImportFrom, ast.Import)):
            lines.append(b)

    for idx in range(len(lines)):
        line = lines[idx]
        if isinstance(line, ast.Import):
            lines[idx] = ast.unparse(line) if _is_import_used(line, used_annotations) else ''
        elif isinstance(line, ast.ImportFrom):
            lines[idx] = ast.unparse(line) if _is_import_from_used(line, used_annotations) else ''

    fdict = '{' + ', '.join(f'"{fname}": {fdef}' for fname, fdef in functions.items()) + '}'

    lines.append('from ' + Definition.__module__ + ' import ' + Definition.__name__ + ', ' + FunctionDef.__name__)
    lines.append(f'dispatcher.definition_complete(Definition("module", {fdict}))')

    body = '\n'.join(lines)
    return body


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
