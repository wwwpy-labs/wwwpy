from dataclasses import dataclass

import pytest

from tests.common import DynSysPath, dyn_sys_path
from wwwpy.common.rpc.v2 import proxy_generator
from wwwpy.common.rpc.v2.dispatcher import TargetType, Dispatcher


@dataclass
class DefinitionCompleteInvoke:
    locals_: dict
    target: TargetType


class DispatcherFake(Dispatcher):
    instances: list['DispatcherFake'] = []

    def __init__(self):
        self.instances.append(self)
        self.definition_complete_invokes = []

    def definition_complete(self, locals_, target: TargetType) -> None:
        invoke = DefinitionCompleteInvoke(locals_, target)
        self.definition_complete_invokes.append(invoke)


source = '''
def add(a: int, b: int) -> int:
    return a + b
    
def sub(a: int, b: int) -> int:
    return a - b
'''
source_async = source.replace('def ', 'async def ')

def test_instantiation(db_fake):
    # WHEN
    gen = proxy_generator.generate(source, DispatcherFake)
    exec(gen)

    # THEN
    assert len(DispatcherFake.instances) == 1

def test_function_definitions():
    # WHEN
    gen = proxy_generator.generate(source, DispatcherFake)

    # THEN
    assert 'def add(a: int, b: int) -> int:' in gen
    assert 'def sub(a: int, b: int) -> int:' in gen

def todo_test_async_function_definitions():
    # WHEN
    gen = proxy_generator.generate(source_async, DispatcherFake)

    # THEN
    assert 'async def add(a: int, b: int) -> int:' in gen
    assert 'async def sub(a: int, b: int) -> int:' in gen

def test_function_type_hints():
    # WHEN
    gen = proxy_generator.generate('def add(a: int, b: int = 123) -> int: pass', DispatcherFake)

    # THEN
    assert 'def add(a: int, b: int=123) -> int:' in gen

def test_definition_complete_called(db_fake):
    # WHEN
    gen = proxy_generator.generate(source, DispatcherFake)
    exec(gen)

    # THEN
    builder = DispatcherFake.instances[0]
    assert len(builder.definition_complete_invokes) == 1
    invoke = builder.definition_complete_invokes[0]
    assert invoke.target == TargetType.module


def test_module_function_generation(db_fake):
    # WHEN
    gen = proxy_generator.generate(source, DispatcherFake)
    exec(gen)

    # THEN
    builder = DispatcherFake.instances[0]
    locals_ = builder.definition_complete_invokes[0].locals_
    assert 'add' in locals_
    assert 'sub' in locals_


def test_function_return_value(db_fake, dyn_sys_path: DynSysPath):
    # GIVEN
    gen = proxy_generator.generate(source, DispatcherFake)
    dyn_sys_path.write_module2('module1.py', gen)

    import module1 # fires the instantiation of the builder

    def dispatch_module_function(*args):
        print(f'dispatching {args}')
        return 42

    builder = DispatcherFake.instances[0]
    builder.dispatch_module_function = dispatch_module_function


    # WHEN invoke add
    res = module1.add(1, 2)

    # THEN
    assert res == 42


@pytest.fixture
def db_fake():
    yield None
    DispatcherFake.instances.clear()
