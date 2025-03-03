import logging
import typing
from types import FunctionType

import pytest

from tests.common import DynSysPath, dyn_sys_path
from wwwpy.common.rpc2.stub_generator import generate_stub, Stub

logger = logging.getLogger(__name__)


class NamespaceFake:
    def __init__(self, calls, name: str = ''):
        self._calls = calls
        self._name = name
        self.return_value = None
        self.class_by_name = {}

    def add_class(self, class_name: str):
        fake = NamespaceFake([])
        self.class_by_name[class_name] = fake
        return fake

    def __getattr__(self, item):
        class_ns = self.class_by_name.get(item, None)
        if class_ns is not None:
            return class_ns

        def function(*args, **kwargs):
            self._calls.append((item, *args))
            return self.return_value

        return function


class StubFake(Stub):
    instances: list['StubFake'] = []

    def __init__(self, *args):
        self.instances.append(self)
        self.args = args
        self.setup_functions_calls: list[tuple[FunctionType, ...]] = []
        self.setup_classes_calls: list[tuple[type, ...]] = []
        self.calls = []
        self.namespace = NamespaceFake(self.calls)

    def setup_functions(self, *functions: FunctionType) -> None:
        self.setup_functions_calls.append(functions)

    def setup_classes(self, *classes: type) -> None:
        self.setup_classes_calls.append(classes)


source_sync = '''
def add(a: int, b: int) -> int:
    return a + b
    
def sub(a: int, b: int) -> int:
    return a - b
'''
source_async = source_sync.replace('def ', 'async def ')

class_sync = '''
class Class1:
    def foo(self, a: int) -> int: return a
    def bar(self, b: str) -> str: return b 
'''


class TestImportForSourceCorrectness:
    def test_blank_source_should_not_fail(self, fixture):
        fixture.generate('', module='module1')
        import module1  # noqa

    def test_instantiation(self, fixture):
        # WHEN
        gen = fixture.generate(source_sync)
        exec(gen)

        # THEN
        assert len(StubFake.instances) == 1


def test_private_functions_should_not_be_generated(fixture):
    fixture.generate('def _private1(a, b): ...', module='module1')

    import module1  # noqa

    # assert '_private1' not in the functions of module1
    assert '_private1' not in module1.__dict__


def test_private_class_should_not_be_generated(fixture):
    fixture.generate('class _Private1: pass', module='module1')

    import module1  # noqa

    # assert '_Private1' not in the classes of module1
    assert '_Private1' not in module1.__dict__


def test_private_method_should_not_be_generated(fixture):
    fixture.generate('class Class1:\n    def _private1(self): pass', module='module1')

    import module1  # noqa

    # assert '_private1' not in the methods of Class1
    assert '_private1' not in dir(module1.Class1)


def test_sync_function_definitions(fixture):
    # WHEN
    gen = fixture.generate(source_sync)

    # THEN
    assert 'def add(a: int, b: int) -> int:' in gen
    assert 'def sub(a: int, b: int) -> int:' in gen


def test_async_function_definitions(fixture):
    # WHEN
    gen = fixture.generate(source_async)

    # THEN
    assert 'async def add(a: int, b: int) -> int:' in gen
    assert 'async def sub(a: int, b: int) -> int:' in gen


def test_sync_method_definitions(fixture):
    # WHEN
    gen = fixture.generate(class_sync)

    # THEN
    assert 'def foo(self, a: int) -> int:' in gen
    assert 'def bar(self, b: str) -> str:' in gen


def test_async_method_definitions(fixture):
    # WHEN
    gen = fixture.generate(class_sync.replace('def ', 'async def '))

    # THEN
    assert 'async def foo(self, a: int) -> int:' in gen
    assert 'async def bar(self, b: str) -> str:' in gen


# def test_definition_complete_function_dictionary(db_fake):
#     # WHEN
#     exec(db_fake.generate(source))
#
#     # THEN
#     assert len(db_fake.builder.definition_complete_invokes) == 1
#     invoke = db_fake.builder.definition_complete_invokes[0]
#     assert set(invoke.functions.keys()) == {'add', 'sub'}
#     add = invoke.functions['add']
#     sub = invoke.functions['sub']
#     print('ok')


# def test_definition_complete_called(db_fake):
def test_setup_functions___called(fixture):
    # WHEN
    gen = fixture.generate(source_sync)
    exec(gen)

    # THEN
    assert len(fixture.builder.setup_functions_calls) == 1
    invoke = fixture.builder.setup_functions_calls[0]
    assert list(map(lambda f: f.__name__, invoke)) == ['add', 'sub']


def test_setup_classes___called(fixture):
    # GIVEN
    fixture.generate('class Class1:\n    def add(self, c: int) -> int: pass', 'module1')

    # WHEN
    import module1  # noqa

    # THEN
    assert len(fixture.builder.setup_classes_calls) == 1
    invoke = fixture.builder.setup_classes_calls[0]
    assert list(map(lambda f: f.__name__, invoke)) == ['Class1']


def test_actual_invocation__sync_function(fixture):
    # GIVEN
    fixture.generate(source_sync, module='module1')
    import module1  # noqa

    fixture.builder.namespace.return_value = 42
    # WHEN
    result = module1.add(1, 2)

    # THEN
    assert fixture.builder.calls == [('add', 1, 2)]
    assert result == 42


async def test_actual_invocation__async_function(fixture):
    # GIVEN
    fixture.generate(source_async, module='module1')
    import module1  # noqa

    async def some_result():
        return 42

    fixture.builder.namespace.return_value = some_result()
    # WHEN
    result = await module1.add(1, 2)

    # THEN
    assert fixture.builder.calls == [('add', 1, 2)]
    assert result == 42


def test_actual_invocation__sync_method(fixture):
    # GIVEN
    fixture.generate(class_sync, module='module1')
    import module1  # noqa

    class1_fake = fixture.builder.namespace.add_class('Class1')
    class1_fake.return_value = 42

    # WHEN
    instance = module1.Class1()
    result = instance.foo(43)

    # THEN
    assert class1_fake._calls == [('foo', instance, 43)]
    assert result == 42


def test_function_type_hints(fixture):
    # WHEN
    gen = fixture.generate('def add(a: int, b: int = 123) -> int: pass')

    # THEN
    assert 'def add(a: int, b: int=123) -> int:' in gen


_person_module = 'module_person.py', '''
from dataclasses import dataclass
@dataclass
class Person:
    name: str
    age: int

class Car: ...
'''


def _verify_type_hints(fun_ref, type_name, expected_type):
    hints = typing.get_type_hints(fun_ref, {})
    assert hints.get(type_name, None) == expected_type


class TestTypeHintsArguments:
    def test_ImportFrom(self, fixture):
        # GIVEN
        fixture.dyn_sys_path.write_module2(*_person_module)
        fixture.generate('from module_person import Person\ndef fun1(p: Person) -> int: ...', module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        self._verify_fun1_p_type_is_person(module1.fun1)

    def test_Import(self, fixture):
        # GIVEN
        fixture.dyn_sys_path.write_module2(*_person_module)
        fixture.generate('import module_person\ndef fun1(p: module_person.Person) -> int: ...', module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        self._verify_fun1_p_type_is_person(module1.fun1)

    def test_should_importOnlyImportsUsedInTypeHints(self, fixture):
        fixture.generate('from module_person import Person\ndef fun1(a: int) -> int: ...', module='module1')

    def test_should_importFrom_multiple(self, fixture):
        fixture.generate('from module_person import Person, Car\ndef fun1(a: int) -> int: ...', module='module1')

    def test_should_importFrom_multiple__one_used(self, fixture):
        fixture.dyn_sys_path.write_module2(*_person_module)
        fixture.generate('from module_person import Person, Car\ndef fun1(a: Person) -> int: ...', module='module1')

    def _verify_fun1_p_type_is_person(self, fun1):
        from module_person import Person  # noqa
        _verify_type_hints(fun1, 'p', Person)


class TestTypeHintsReturn:
    def test_return_type(self, fixture):
        # GIVEN
        fixture.generate(source_sync, module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        _verify_type_hints(module1.add, 'return', int)
        _verify_type_hints(module1.sub, 'return', int)

    def test_return_complex_type(self, fixture):
        # GIVEN
        fixture.dyn_sys_path.write_module2(*_person_module)
        fixture.generate('from module_person import Person\ndef fun1() -> Person: ...', module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        from module_person import Person  # noqa
        _verify_type_hints(module1.fun1, 'return', Person)

    def test_return_no_type_hint_is_the_same_as_None(self, fixture):
        # GIVEN
        fixture.generate('def fun1(): ...', module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        _verify_type_hints(module1.fun1, 'return', None)


class TestDispatcherArgs:
    def test_arg_simple_string(self, fixture):
        # GIVEN
        gen = generate_stub('def some(a:int)->int: ...', StubFake, "'s1', 's2'")
        fixture.dyn_sys_path.write_module2('module1.py', gen)

        # WHEN
        import module1  # noqa

        # THEN
        assert fixture.builder.args == ('s1', 's2')

    def test_arg_dict(self, fixture):
        # GIVEN
        args = "{'url': 'some-url', 'some-int': 42}"
        gen = generate_stub('def some(a:int)->int: ...', StubFake, args)
        fixture.dyn_sys_path.write_module2('module1.py', gen)

        # WHEN
        import module1  # noqa

        # THEN
        assert fixture.builder.args == ({'url': 'some-url', 'some-int': 42},)


class Fixture:
    def __init__(self, dyn_sys_path: DynSysPath):
        self.dyn_sys_path = dyn_sys_path

    def generate(self, src: str, module=None) -> str:
        gen = generate_stub(src, StubFake)
        if module is not None:
            self.dyn_sys_path.write_module2(f'{module}.py', gen)
            logger.debug(f'Generated module {module}:\n{gen}')
        return gen

    @property
    def builder(self):
        assert len(StubFake.instances) == 1
        return StubFake.instances[0]


@pytest.fixture
def fixture(dyn_sys_path: DynSysPath):
    f = Fixture(dyn_sys_path)
    yield f
    StubFake.instances.clear()


class TestFake:
    def test_simple_call(self):
        # GIVEN
        calls = []
        target = NamespaceFake(calls)

        # WHEN
        target.something(42)

        # THEN
        assert calls == [('something', 42)]

    async def test_return_async(self):
        # GIVEN
        target = NamespaceFake([])

        async def async_call():
            return 42

        target.return_value = async_call()

        # WHEN
        result = await target.some()

        # THEN
        assert result == 42

    def test_add_class(self):
        # GIVEN
        target = NamespaceFake([])

        # WHEN
        target.add_class('Class1')
        target.Class1.some_method(42)

        # THEN
        assert target.Class1._calls == [('some_method', 42)]

    def test_class_return_value(self):
        # GIVEN
        target = NamespaceFake([])
        target.add_class('Class1').return_value = 42

        # WHEN
        result = target.Class1.some()

        # THEN
        assert result == 42
