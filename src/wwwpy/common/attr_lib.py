import ast
import inspect
from collections.abc import Callable


class _AttrVisitor(ast.NodeVisitor):
    def __init__(self):
        self.attr = None

    def visit_Lambda(self, node):
        # Only support simple attribute access: lambda x: x.foo
        if isinstance(node.body, ast.Attribute):
            self.attr = node.body.attr

    def visit_FunctionDef(self, node):
        # Only support simple attribute access: def foo(x): return x.bar
        if len(node.body) == 1 and isinstance(node.body[0], ast.Return):
            ret = node.body[0].value
            if isinstance(ret, ast.Attribute):
                self.attr = ret.attr

def attr_name(block: Callable) -> str:
    src = inspect.getsource(block).strip()
    visitor = _AttrVisitor()
    visitor.visit(ast.parse(src))
    if visitor.attr is None:
        raise ValueError("Callable must be of the form: lambda x: x.foo or def foo(x): return x.bar")
    return visitor.attr


def test_attr_name_with_lambda():
    result = attr_name(lambda x: x.foo)
    assert result == "foo"


def test_attr_name_with_function():
    def foo(x):
        return x.bar

    result = attr_name(foo)
    assert result == "bar"
