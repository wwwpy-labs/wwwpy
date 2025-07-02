from dataclasses import dataclass
from typing import List

from wwwpy.common import property_monitor as pm
from wwwpy.common.property_monitor import PropertyChanged, monitor_changes, set_origin, Monitorable, Monitor
from wwwpy.common.rpc import serialization


@dataclass
class DataclassStub:
    name: str = ""
    value: int = 0


def test_monitor_existing_property_change():
    events: List[List[PropertyChanged]] = []

    def on_change(changes: List[PropertyChanged]):
        events.append(changes)

    obj = DataclassStub("bob", 10)
    monitor_changes(obj, on_change)

    obj.value = 20

    assert events == [[PropertyChanged(obj, "value", 10, 20)]]


def test_monitor_on_second_instance():
    events1: List[List[PropertyChanged]] = []
    events2: List[List[PropertyChanged]] = []

    def on_change1(changes: List[PropertyChanged]):
        events1.append(changes)

    def on_change2(change2: List[PropertyChanged]):
        events2.append(change2)

    obj1 = DataclassStub("alice", 10)
    monitor_changes(obj1, on_change1)
    obj2 = DataclassStub("bob", 20)
    monitor_changes(obj2, on_change2)

    obj1.value = 1

    assert events1 == [[PropertyChanged(obj1, "value", 10, 1)]]
    assert events2 == []

    obj2.value = 2

    assert events1 == [[PropertyChanged(obj1, "value", 10, 1)]]
    assert events2 == [[PropertyChanged(obj2, "value", 20, 2)]]


def test_event_should_fire_after_property_change():
    obj = DataclassStub("alice", 10)

    def on_change(_):
        assert obj.value == 1

    monitor_changes(obj, on_change)

    obj.value = 1


def test_double_monitor__should_add_listener():
    events1: List[List[PropertyChanged]] = []
    events2: List[List[PropertyChanged]] = []

    obj = DataclassStub("alice", 10)

    monitor_changes(obj, lambda change: events1.append(change))
    monitor_changes(obj, lambda change: events2.append(change))

    obj.value = 1

    assert events1 == [[PropertyChanged(obj, "value", 10, 1)]]


# todo add test to verify that an exception is thrown when trying to group on an unmonitored object
def test_group_changes():
    events: List[List[PropertyChanged]] = []

    def on_change(changes: List[PropertyChanged]):
        events.append(changes)

    obj = DataclassStub("alice", 10)
    monitor_changes(obj, on_change)

    with pm.group_changes(obj):
        obj.value = 1
        assert events == []
        obj.name = "bob"
        assert events == []

    assert events == [[PropertyChanged(obj, "value", 10, 1), PropertyChanged(obj, "name", "alice", "bob")]]
    events.clear()

    # verify immediate delivery of changes
    obj.value = 123
    assert events == [[PropertyChanged(obj, "value", 1, 123)]]


def test_deserialize():
    def on_change(changes: List[PropertyChanged]):
        raise Exception("Should not be called")

    obj = DataclassStub("alice", 10)
    monitor_changes(obj, on_change)

    serialized = serialization.serialize(obj, DataclassStub)
    deserialized = serialization.deserialize(serialized, DataclassStub)

    assert deserialized == obj


def test_with_origin():
    obj = DataclassStub("alice", 10)
    events: List[List[PropertyChanged]] = []
    monitor_changes(obj, lambda changes: events.append(changes))

    with set_origin(obj, 'some_origin'):
        obj.value = 123

    assert events == [[PropertyChanged(obj, "value", 10, 123, 'some_origin')]]


def test_get_monitor_should_honor_HasMonitor():
    m = Monitor()

    class SomeMonitored(Monitorable):
        pass

    obj = SomeMonitored()
    assert pm.get_monitor(obj) == m


def test_get_monitor_or_create():
    # needs to be local because the monitor changes the definition of the class!
    @dataclass
    class TestClass:
        name: str = ""
        value: int = 0

    obj = TestClass("alice", 10)
    m = pm.get_monitor_or_create(obj)
    assert pm.get_monitor(obj) == m

    events = []
    m.listeners.append(lambda changes: events.append(changes))

    obj.value = 123

    assert events == [[PropertyChanged(obj, "value", 10, 123)]]


def test_attr_listener():
    obj = DataclassStub("alice", 10)
    events: List[List[PropertyChanged]] = []
    pm.get_monitor_or_create(obj).add_attribute_listener('name', lambda change: events.append(change))

    obj.value = 123

    assert events == []

    obj.name = "bob"
    assert events == [[PropertyChanged(obj, "name", "alice", "bob")]]


def test_attr_listener_with_grouping():
    obj = DataclassStub("alice", 10)
    events: List[List[PropertyChanged]] = []
    m = pm.get_monitor_or_create(obj)
    m.add_attribute_listener('name', lambda change: events.append(change))

    with pm.group_changes(obj):
        obj.name = "bob"
        assert events == []
        obj.value = 123
        assert events == []
        obj.name = "carol"
        assert events == []

    assert events == [[PropertyChanged(obj, "name", "alice", "bob"), PropertyChanged(obj, "name", "bob", "carol")]]


def todo_test_monitorable_inheritance_simple_class():
    class TestClass(Monitorable):
        name: str = ""
        value: int = 10

    obj = TestClass()
    m = pm.get_monitor_or_create(obj)
    assert obj.monitor_object == m

    events = []
    m.listeners.append(lambda changes: events.append(changes))

    obj.value = 123

    assert events == [[PropertyChanged(obj, "value", 10, 123)]]


class GetterSetterStub:
    def __init__(self, name: str = '', value: int = 0):
        self._name = name
        self._value = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: int):
        self._value = value


class TestOnGetterSetter:
    def test_monitor_existing_property_change(self):
        events: List[List[PropertyChanged]] = []

        def on_change(changes: List[PropertyChanged]):
            events.append(changes)

        obj = GetterSetterStub("bob", 10)
        monitor_changes(obj, on_change)

        obj.value = 20

        assert events == [[PropertyChanged(obj, "value", 10, 20)]]


class PlainOldPythonObject:
    def __init__(self, name: str = '', value: int = 0):
        self.name = name
        self.value = value


class TestOnPlainOldPythonObject:
    def test_monitor_existing_property_change(self):
        events: List[List[PropertyChanged]] = []

        def on_change(changes: List[PropertyChanged]):
            events.append(changes)

        obj = PlainOldPythonObject("bob", 10)
        monitor_changes(obj, on_change)

        obj.value = 20

        assert events == [[PropertyChanged(obj, "value", 10, 20)]]
