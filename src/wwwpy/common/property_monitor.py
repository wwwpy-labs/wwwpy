from dataclasses import dataclass, field
from typing import Callable, List, Optional
from contextlib import contextmanager


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
    grouping: Optional[List[PropertyChanged]] = None
    origin: Optional[any] = None

    def notify(self, changes: List[PropertyChanged]):
        if self.grouping is not None:
            self.grouping.extend(changes)
        else:
            for l in self.listeners:
                l(changes)


__instance_monitor_attr = "__instance_monitor_attr"


def has_monitor(instance):
    return hasattr(instance, __instance_monitor_attr)


def get_monitor(instance) -> Optional[Monitor]:
    return getattr(instance, __instance_monitor_attr, None)


def get_monitor_or_raise(instance) -> Monitor:
    m = get_monitor(instance)
    if m is None:
        raise Exception("No monitor found")
    return m


# todo should return un unsubscribe function
def monitor_changes(instance, on_changed: Callable[[List[PropertyChanged]], None]):
    """Monitor the changes of the properties of an instance of a class."""

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

    if has_monitor(instance):
        m: Monitor = instance.__instance_monitor_attr
    else:
        m = Monitor()
        instance.__instance_monitor_attr = m

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
