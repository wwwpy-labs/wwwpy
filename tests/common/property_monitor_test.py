from dataclasses import dataclass
from typing import List

from wwwpy.common import property_monitor as pm
from wwwpy.common.property_monitor import PropertyChanged, monitor_changes
import pytest

from wwwpy.common.rpc import serialization


@dataclass
class TestClass:
    name: str = ""
    value: int = 0


def test_monitor_existing_property_change():
    events: List[List[PropertyChanged]] = []

    def on_change(changes: List[PropertyChanged]):
        events.append(changes)

    obj = TestClass("bob", 10)
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

    obj1 = TestClass("alice", 10)
    monitor_changes(obj1, on_change1)
    obj2 = TestClass("bob", 20)
    monitor_changes(obj2, on_change2)

    obj1.value = 1

    assert events1 == [[PropertyChanged(obj1, "value", 10, 1)]]
    assert events2 == []

    obj2.value = 2

    assert events1 == [[PropertyChanged(obj1, "value", 10, 1)]]
    assert events2 == [[PropertyChanged(obj2, "value", 20, 2)]]


def test_event_should_fire_after_property_change():
    obj = TestClass("alice", 10)

    def on_change(_):
        assert obj.value == 1

    monitor_changes(obj, on_change)

    obj.value = 1


def test_double_monitor__should_raise_exception():
    obj = TestClass("alice", 10)
    monitor_changes(obj, lambda change: None)
    with pytest.raises(Exception):
        monitor_changes(obj, lambda change: None)

# todo add test to verify that an exception is thrown when trying to group on an unmonitored object
def test_group_changes():
    events: List[List[PropertyChanged]] = []

    def on_change(changes: List[PropertyChanged]):
        events.append(changes)

    obj = TestClass("alice", 10)
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

    obj = TestClass("alice", 10)
    monitor_changes(obj, on_change)

    serialized = serialization.serialize(obj, TestClass)
    deserialized = serialization.deserialize(serialized, TestClass)

    assert deserialized == obj
