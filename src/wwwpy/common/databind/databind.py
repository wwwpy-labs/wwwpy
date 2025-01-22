from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from wwwpy.common.property_monitor import Monitor, PropertyChanged, set_origin, monitor_changes, Monitorable


@dataclass
class TargetOriginEvent:
    origin_target: TargetAdapter
    value: any


# todo rename to BindingTarget?
class TargetAdapter(Monitorable):

    def __init__(self):
        self.monitor = Monitor()
        super().__init__()

    def get_property_monitor(self):
        return self.monitor

    def set_target_value(self, value):
        pass

    def get_target_value(self):
        pass



class Binding:

    def __init__(self, source, attr_name, target_adapter: TargetAdapter):
        super().__init__()
        self.source = source
        self.attr_name = attr_name
        self.target_adapter = target_adapter
        target_adapter.monitor.listeners.append(self._on_target_changes)
        monitor_changes(source, self._on_source_changes)

    def apply_binding(self):
        self.target_adapter.set_target_value(getattr(self.source, self.attr_name))

    def _on_target_changes(self, events: List[PropertyChanged]):
        event = events[-1]
        with set_origin(self.source, self):
            setattr(self.source, self.attr_name, event.new_value)

    def _on_source_changes(self, events: List[PropertyChanged]):
        event = events[-1]
        if event.origin == self:
            return
        with set_origin(self.target_adapter, self):
            self.target_adapter.set_target_value(event.new_value)
