import logging

import pytest

from tests.common import DynSysPath, dyn_sys_path
from wwwpy.common.rpc.v2.dispatcher import Dispatcher, Definition
from wwwpy.common.rpc2.stub_generator import caller_proxy_generate

logger = logging.getLogger(__name__)


class DispatcherFake(Dispatcher):
    instances: list['DispatcherFake'] = []

    def __init__(self, *args):
        self.instances.append(self)
        self.args = args
        self.definition_complete_invokes: list[Definition] = []

    def definition_complete(self, definition: Definition) -> None:
        self.definition_complete_invokes.append(definition)


source = '''
def add(a: int, b: int) -> int:
    return a + b
    
def sub(a: int, b: int) -> int:
    return a - b
'''
source_async = source.replace('def ', 'async def ')


def test_blank_source_should_not_fail(db_fake):
    db_fake.generate('', module='module1')
    import module1  # noqa


def test_private_functions_should_not_be_generated(db_fake):
    db_fake.generate('def _private1(a, b): ...', module='module1')

    import module1  # noqa

    assert '_private1' not in db_fake.definition.functions


def test_instantiation(db_fake):
    # WHEN
    gen = db_fake.generate(source)
    exec(gen)

    # THEN
    assert len(DispatcherFake.instances) == 1


def test_function_definitions(db_fake):
    # WHEN
    gen = db_fake.generate(source)

    # THEN
    assert 'def add(a: int, b: int) -> int:' in gen
    assert 'def sub(a: int, b: int) -> int:' in gen


def test_definition_complete_function_dictionary(db_fake):
    # WHEN
    exec(db_fake.generate(source))

    # THEN
    assert len(db_fake.builder.definition_complete_invokes) == 1
    invoke = db_fake.builder.definition_complete_invokes[0]
    assert set(invoke.functions.keys()) == {'add', 'sub'}
    add = invoke.functions['add']
    sub = invoke.functions['sub']
    print('ok')


def test_async_function_definitions(db_fake):
    # WHEN
    gen = db_fake.generate(source_async)

    # THEN
    assert 'async def add(a: int, b: int) -> int:' in gen
    assert 'async def sub(a: int, b: int) -> int:' in gen


async def test_async_call(db_fake):
    # GIVEN
    db_fake.generate(source_async, module='module1')

    import module1  # noqa

    async def dispatch(name, *args):
        assert name == 'add'
        assert args == (1, 2)
        return 42

    db_fake.builder.dispatch_async = dispatch

    # WHEN invoke add
    assert await module1.add(1, 2) == 42


def test_function_type_hints(db_fake):
    # WHEN
    gen = db_fake.generate('def add(a: int, b: int = 123) -> int: pass')

    # THEN
    assert 'def add(a: int, b: int=123) -> int:' in gen


def test_definition_complete_called(db_fake):
    # WHEN
    gen = db_fake.generate(source)
    exec(gen)

    # THEN
    assert len(db_fake.builder.definition_complete_invokes) == 1
    invoke = db_fake.builder.definition_complete_invokes[0]
    assert invoke.target == 'module'


def test_module_function_generation(db_fake):
    # WHEN
    gen = db_fake.generate(source)
    exec(gen)

    # THEN
    assert 'add' in db_fake.definition.functions
    assert 'sub' in db_fake.definition.functions


def test_function_return_value(db_fake):
    # GIVEN
    db_fake.generate(source, module='module1')

    import module1  # noqa

    def dispatch_module_function(*args):
        return 42

    db_fake.builder.dispatch_sync = dispatch_module_function

    # WHEN invoke add
    res = module1.add(1, 2)

    # THEN
    assert res == 42


def test_function_args_values_and_type_hint(db_fake):
    # GIVEN
    db_fake.generate(source, module='module1')

    import module1  # noqa

    assert db_fake.definition.functions['add'].annotations == [int, int]
    assert db_fake.definition.functions['sub'].annotations == [int, int]

    def dispatch_module_function(name, *args):
        assert name == 'add'
        assert args == (1, 2)
        return 'ignored'

    db_fake.builder.dispatch_sync = dispatch_module_function

    # WHEN invoke add
    module1.add(1, 2)

    # THEN
    # the type hint should be as expected


_person_module = 'module_person.py', '''
from dataclasses import dataclass
@dataclass
class Person:
    name: str
    age: int

class Car: ...
'''


class TestImports:
    def test_ImportFrom(self, db_fake):
        # GIVEN
        db_fake.dyn_sys_path.write_module2(*_person_module)
        db_fake.generate('from module_person import Person\ndef fun1(p: Person) -> int: ...', module='module1')

        import module1  # noqa
        from module_person import Person  # noqa
        person = Person('John', 42)

        assert db_fake.definition.functions['fun1'].annotations == [Person]

        def dispatch_module_function(name, *args):
            assert name == 'fun1'
            assert args == (person,)
            return 'ignored'

        db_fake.builder.dispatch_sync = dispatch_module_function

        # WHEN invoke add
        module1.fun1(person)

        # THEN
        # the type hint should be as expected

    def test_Import(self, db_fake):
        # GIVEN
        db_fake.dyn_sys_path.write_module2(*_person_module)
        db_fake.generate('import module_person\ndef fun1(p: module_person.Person) -> int: ...', module='module1')

        import module1  # noqa
        from module_person import Person  # noqa
        person = Person('John', 42)

        assert db_fake.definition.functions['fun1'].annotations == [Person]

        def dispatch_module_function(name, *args):
            assert name == 'fun1'
            assert args == (person,)
            return 'ignored'

        db_fake.builder.dispatch_sync = dispatch_module_function

        # WHEN invoke add
        module1.fun1(person)

        # THEN
        # the type hint should be as expected

    def test_should_importOnlyImportsUsedInTypeHints(self, db_fake):
        db_fake.generate('from module_person import Person\ndef fun1(a: int) -> int: ...', module='module1')

    def test_should_importFrom_multiple(self, db_fake):
        db_fake.generate('from module_person import Person, Car\ndef fun1(a: int) -> int: ...', module='module1')

    def test_should_importFrom_multiple__one_used(self, db_fake):
        db_fake.dyn_sys_path.write_module2(*_person_module)
        db_fake.generate('from module_person import Person, Car\ndef fun1(a: Person) -> int: ...', module='module1')


class TestReturn:
    def test_return_type(self, db_fake):
        # GIVEN
        db_fake.generate(source, module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        assert db_fake.definition.functions['add'].return_annotation == int
        assert db_fake.definition.functions['sub'].return_annotation == int

    def test_return_complex_type(self, db_fake):
        # GIVEN
        db_fake.dyn_sys_path.write_module2(*_person_module)
        db_fake.generate('from module_person import Person\ndef fun1() -> Person: ...', module='module1')

        # WHEN
        import module1  # noqa
        from module_person import Person  # noqa

        # THEN
        assert db_fake.definition.functions['fun1'].return_annotation == Person

    def test_return_no_type_hint_is_the_same_as_None(self, db_fake):
        # GIVEN
        db_fake.generate('def fun1(): ...', module='module1')

        # WHEN
        import module1  # noqa

        # THEN
        assert db_fake.definition.functions['fun1'].return_annotation is None


class TestDispatcherArgs:
    def test_arg_simple_string(self, db_fake):
        # GIVEN
        gen = caller_proxy_generate('def some(a:int)->int: ...', DispatcherFake, "'s1', 's2'")
        db_fake.dyn_sys_path.write_module2('module1.py', gen)

        # WHEN
        import module1  # noqa

        # THEN
        assert db_fake.builder.args == ('s1', 's2')

    def test_arg_dict(self, db_fake):
        # GIVEN
        args = "{'url': 'some-url', 'some-int': 42}"
        gen = caller_proxy_generate('def some(a:int)->int: ...', DispatcherFake, args)
        db_fake.dyn_sys_path.write_module2('module1.py', gen)

        # WHEN
        import module1  # noqa

        # THEN
        assert db_fake.builder.args == ({'url': 'some-url', 'some-int': 42},)


class DbFake:
    def __init__(self, dyn_sys_path: DynSysPath):
        self.dyn_sys_path = dyn_sys_path

    def generate(self, src: str, module=None) -> str:
        gen = caller_proxy_generate(src, DispatcherFake)
        if module is not None:
            self.dyn_sys_path.write_module2(f'{module}.py', gen)
            logger.debug(f'Generated module {module}:\n{gen}')
        return gen

    @property
    def builder(self):
        assert len(DispatcherFake.instances) == 1
        return DispatcherFake.instances[0]

    @property
    def definition(self) -> Definition:
        b = self.builder
        assert len(b.definition_complete_invokes) == 1
        return b.definition_complete_invokes[0]


@pytest.fixture
def db_fake(dyn_sys_path: DynSysPath):
    dbf = DbFake(dyn_sys_path)
    yield dbf
    DispatcherFake.instances.clear()
