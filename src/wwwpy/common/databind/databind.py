from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from wwwpy.common.property_monitor import Monitor, PropertyChanged, set_origin, monitor_changes, Monitorable, \
    get_monitor_or_create


@dataclass
class TargetOriginEvent:
    origin_target: TargetAdapter
    value: any


# todo rename to BindingTarget or Bindable or BindableTarget?
class TargetAdapter(Monitorable):

    def __init__(self):
        super().__init__()

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
        target_adapter.monitor_object.listeners.append(self._on_target_changes)
        get_monitor_or_create(source).add_attribute_listener(attr_name, self._on_source_changes)

    def apply_binding(self):
        self.target_adapter.set_target_value(getattr(self.source, self.attr_name))

    def _on_target_changes(self, events: List[PropertyChanged]):
        event = events[-1]
        with set_origin(self.source, self):
            setattr(self.source, self.attr_name, event.new_value)

    def _on_source_changes(self, events: List[PropertyChanged]):
        event = events[-1]  # todo we should filter only for the attr_name!
        if event.origin == self:
            return
        with set_origin(self.target_adapter, self):
            self.target_adapter.set_target_value(event.new_value)
