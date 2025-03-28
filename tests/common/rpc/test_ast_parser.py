from __future__ import annotations

import ast

from tests.common.rpc.test_rpc import support1_module_name
from wwwpy.common.rpc import func_registry
from wwwpy.websocket import DispatchEndpoint


def test_ast_function_len():
    target = func_registry.from_package_name(support1_module_name)

    # THEN
    assert target.name == 'tests.common.rpc.support1'
    assert len(target.functions) == 2


def test_ast_module_function0():
    # WHEN
    target = func_registry.from_package_name(support1_module_name)

    # THEN
    fun = target.functions[0]
    assert fun.name == 'support1_function0'
    assert fun.signature == '(a: int, b: int) -> int'
    assert not fun.is_coroutine_function


def test_ast_module_function1():
    # WHEN
    target = func_registry.from_package_name(support1_module_name)

    # THEN
    fun = target.functions[1]
    assert fun.name == 'support1_function1'
    assert fun.signature == '(a: int, b: float) -> str'
    assert fun.is_coroutine_function


class MockDispatchEndpoint(DispatchEndpoint):

    def __init__(self, messages):
        self.messages = messages

    def dispatch(self, module: str, func_name: str, *args) -> None:
        self.messages.append((module, func_name, *args))


def test_ast_module_source_to_proxy_no_arguments():
    mod_name = "mod1"
    # language=Python
    target = func_registry.source_to_proxy(mod_name, """
import js
class Class1:
    def alert(self) -> None:
        js.alert('hello')
    """)
    ast.parse(target)  # verify it's a valid python code

    # exec the generated code
    executed = dict()
    exec(target, executed)
    assert 'Class1' in executed

    messages = []
    c = executed['Class1'](MockDispatchEndpoint(messages))
    c.alert()

    assert messages == [(mod_name, 'Class1.alert')]


def test_ast_module_source_to_proxy_with_arguments():
    mod_name = 'mod2'
    # language=Python
    target = func_registry.source_to_proxy(mod_name, """
import js
class Class1:
    def alert(self, message:str) -> None:
        js.alert(message)
    """)
    ast.parse(target)  # verify it's a valid python code

    # exec the generated code
    executed = dict()
    exec(target, executed)
    assert 'Class1' in executed

    messages = []

    c = executed['Class1'](MockDispatchEndpoint(messages))
    c.alert('foo')

    assert messages == [(mod_name, 'Class1.alert', 'foo')]


def test_ast_module_source_to_proxy_with_class_level_assignment():
    mod_name = 'mod2'
    # language=Python
    target = func_registry.source_to_proxy(mod_name, """
import js
class Class1:
    some = 12       
    """)
    ast.parse(target)  # verify it's a valid python code

    # exec the generated code
    executed = dict()
    exec(target, executed)
    assert 'Class1' in executed
    assert 'some' not in executed['Class1'].__dict__
