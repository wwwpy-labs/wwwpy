from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import Callable

from . import code_edit
from . import code_info
from . import element_library as el
from . import element_path as ep


class AttributeEditor(ABC):
    definition: el.AttributeDef
    exists: bool
    value: str | None


class EventEditor:
    definition: el.EventDef
    handled: bool = False

    def __init__(self, event_def: el.EventDef, handled: bool, method_name: str,
                 _do_action: Callable[[EventEditor], None]):
        self.handled = handled
        self.definition = event_def
        self.method_name = method_name
        self._do_action = _do_action

    def do_action(self):
        """If the class does not have the method, add it.
        In any case it should focus the IDE cursor on the method.
        """
        self._do_action(self)


class ElementEditor:
    attributes: list[AttributeEditor]
    events: list[EventEditor]

    def __init__(self, element_path: ep.ElementPath, element_def: el.ElementDef):
        self.events = []
        self.element_path = element_path
        ci = code_info.class_info(self._python_source(), element_path.class_name)
        data_name = element_path.data_name
        for event in element_def.events:
            method_name = f'{data_name}__{event.name}'
            method = ci.methods_by_name.get(method_name, None)
            event_editor = EventEditor(event, True if method else False, method_name, self._event_do_action)
            self.events.append(event_editor)

    def _python_source(self):
        return Path(self.element_path.concrete_path).read_text()

    def _event_do_action(self, event_editor: EventEditor):
        new_source = code_edit.add_method(self._python_source(), self.element_path.class_name,
                                          event_editor.method_name, 'event')
        Path(self.element_path.concrete_path).write_text(new_source)