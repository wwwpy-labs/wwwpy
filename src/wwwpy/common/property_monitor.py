from dataclasses import dataclass, field
from typing import Callable, List, Optional
from contextlib import contextmanager


@dataclass
class PropertyChanged:
    instance: any
    name: str
    old_value: object
    new_value: object


@dataclass
class Monitor:
    listeners: list[Callable[[List[PropertyChanged]], None]] = field(default_factory=list)
    grouping: Optional[List[PropertyChanged]] = None

    def notify(self, changes: List[PropertyChanged]):
        if self.grouping is not None:
            self.grouping.extend(changes)
        else:
            for l in self.listeners:
                l(changes)


__instance_monitor_attr = "__instance_monitor_attr"

def has_monitor(instance):
    return hasattr(instance, __instance_monitor_attr)

def monitor_changes(instance, on_changed: Callable[[List[PropertyChanged]], None]):
    """Monitor the changes of the properties of an instance of a class."""

    clazz = instance.__class__
    if not hasattr(clazz, "__attr_change_monitor"):
        setattr(clazz, "__attr_change_monitor", True)

        original_setattr = clazz.__setattr__  # Keep a reference to the original method

        def new_setattr(self, name, value):
            old_value = getattr(self, name, None)
            original_setattr(self, name, value)
            if name == __instance_monitor_attr or not has_monitor(self):
                return

            change = PropertyChanged(self, name, old_value, value)
            m: Monitor = self.__instance_monitor_attr
            m.notify([change])

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

    m: Monitor = instance.__instance_monitor_attr
    buffer = []
    m.grouping = buffer

    try:
        yield instance
    finally:
        m.grouping = None
        if buffer:
            m.notify(buffer)
