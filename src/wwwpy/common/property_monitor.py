from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from contextlib import contextmanager


class Monitorable:
    def __init__(self):
        self.monitor_object = Monitor()


# todo rename to AttributeChanged
@dataclass
class PropertyChanged:
    instance: any
    name: str
    old_value: object
    new_value: object
    origin: Optional[any] = None


@dataclass
class _OriginEvent:
    value: any
    origin: any


# in other situations we could make this a class to be inherited from, so to handle the
# general mechanism of monitoring changes
@dataclass
class Monitor:
    listeners: list[Callable[[List[PropertyChanged]], None]] = field(default_factory=list)
    attr_listeners: dict[str, List[Callable[[List[PropertyChanged]], None]]] = field(default_factory=dict)
    grouping: Optional[List[PropertyChanged]] = None
    origin: Optional[any] = None

    def add_attribute_listener(self, attr_name: str, listener: Callable[[List[PropertyChanged]], None]):
        if attr_name not in self.attr_listeners:
            self.attr_listeners[attr_name] = []
        self.attr_listeners[attr_name].append(listener)

    def notify(self, changes: List[PropertyChanged]):

        if self.grouping is not None:
            self.grouping.extend(changes)
            return

        for l in self.listeners:
            l(changes)
        d = _group_by_attr_name(changes)
        for attr_name, listeners in self.attr_listeners.items():
            if attr_name in d:
                for l in listeners:
                    l(d[attr_name])


def _group_by_attr_name(changes: List[PropertyChanged]):
    d = defaultdict(list)
    for u in changes:
        d[str(u.name)].append(u)
    return dict(d)


__instance_monitor_attr = "__instance_monitor_attr"


def has_monitor(instance):
    return get_monitor(instance) is not None


def get_monitor(instance) -> Optional[Monitor]:
    if isinstance(instance, Monitorable):
        return instance.monitor_object
    return getattr(instance, __instance_monitor_attr, None)


def get_monitor_or_create(instance) -> Monitor:
    m = get_monitor(instance)
    if m is not None:
        return m
    clazz = instance.__class__

    if not hasattr(clazz, "__attr_change_monitor"):
        setattr(clazz, "__attr_change_monitor", True)

        original_setattr = clazz.__setattr__  # Keep a reference to the original method

        def new_setattr(self, name, value):
            old_value = getattr(self, name, None)
            original_setattr(self, name, value)

            monitor = get_monitor(self)
            if monitor is None:
                return
            change = PropertyChanged(self, name, old_value, value, monitor.origin)
            monitor.notify([change])

        clazz.__setattr__ = new_setattr

    m = Monitor()
    instance.__instance_monitor_attr = m
    return m


def get_monitor_or_raise(instance) -> Monitor:
    m = get_monitor(instance)
    if m is None:
        raise Exception("No monitor found")
    return m


# todo should return un unsubscribe function
def monitor_changes(instance, on_changed: Callable[[List[PropertyChanged]], None]):
    """Monitor the changes of the properties of an instance of a class."""

    m = get_monitor_or_create(instance)
    m.listeners.append(on_changed)


@contextmanager
def group_changes(instance):
    # what happens with nested groupings?

    m: Monitor = get_monitor_or_raise(instance)
    buffer = []
    m.grouping = buffer

    try:
        yield instance
    finally:
        m.grouping = None
        if buffer:
            m.notify(buffer)


@contextmanager
def set_origin(instance, origin: any):
    monitor = get_monitor_or_raise(instance)
    monitor.origin = origin
    try:
        yield instance
    finally:
        monitor.origin = None
