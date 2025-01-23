from dataclasses import dataclass

from wwwpy.common.databind.databind import Binding, TargetAdapter
from wwwpy.common.property_monitor import PropertyChanged, group_changes


@dataclass
class User:
    name: str
    age: int = 42


@dataclass
class Car:
    color: str


def test_databind_input_string1():
    # GIVEN
    tag1 = _new_target_adapter()
    user = User('foo1')

    # WHEN
    _bind(user, 'name', tag1)

    # THEN
    assert tag1.input.value == 'foo1'


def test_databind_input_string2():
    # GIVEN
    tag1 = _new_target_adapter()
    car1 = Car('yellow')

    # WHEN
    _bind(car1, 'color', tag1)

    # THEN
    assert tag1.input.value == 'yellow'


def test_databind_input_string__target_to_source():
    # GIVEN
    tag1 = _new_target_adapter()
    car1 = Car('')

    # WHEN
    _bind(car1, 'color', tag1)

    tag1.press_sequentially('yellow1')

    # THEN
    assert car1.color == 'yellow1'


class TestTwoWayBinding:

    def test_databind_input_string__source_to_target(self):
        tag1 = _new_target_adapter()
        tag2 = _new_target_adapter()
        user = User('')

        _bind(user, 'name', tag1)
        _bind(user, 'name', tag2)

        tag1.press_sequentially('foo1')

        assert tag1.input.value == 'foo1'
        assert tag2.input.value == 'foo1'


    def test_databind_two_different_fields(self):
        tag1 = _new_target_adapter()
        tag2 = _new_target_adapter()
        tag3 = _new_target_adapter()
        user = User('')

        _bind(user, 'name', tag1)
        # _bind(user, 'name', tag2)
        _bind(user, 'age', tag3)

        with group_changes(user):
            user.name = 'foo1'
            user.age = 43


        assert tag3.input.value == 43
        assert tag1.input.value == 'foo1'


def _bind(instance, attr_name, target_adapter):
    target = Binding(instance, attr_name, target_adapter)
    target.apply_binding()


@dataclass
class FakeInput:
    value: str = ''


class FakeInputTargetAdapter(TargetAdapter):
    def __init__(self):
        super().__init__()
        self.input = FakeInput()

    def set_target_value(self, value):
        self.input.value = value

    def get_target_value(self):
        return self.input.value

    def press_sequentially(self, value):
        for ch in value:
            self.input.value += ch
            # todo this doesn't look right; is it appropriate passing '' for the attr_name?
            self.monitor.notify([PropertyChanged(self, '', None, self.input.value)])


def _new_target_adapter():
    return FakeInputTargetAdapter()
