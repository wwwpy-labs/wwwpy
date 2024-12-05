from __future__ import annotations

from abc import ABC
from typing import Callable

from . import code_edit, code_strings, html_edit, html_locator
from . import code_info
from . import element_library as el
from . import element_path as ep
from .. import modlib
from ..collectionlib import ListMap


class AttributeEditor(ABC):
    """Allow to add/edit/remove attributes of an HTML element according to its AttributeDef."""

    @property
    def definition(self) -> el.AttributeDef:
        return self._definition

    @property
    def exists(self) -> bool:
        return self._exists

    def remove(self):
        self._remove(self)

    @property
    def value(self) -> str | None:
        return self._value

    @value.setter
    def value(self, value: str | None):
        self._set_value(self, value)

    def __init__(self, definition: el.AttributeDef, exists: bool, value: str | None,
                 set_value: Callable[[AttributeEditor, str | None], None],
                 remove: Callable[[AttributeEditor], None]
                 ):
        self._definition = definition  # readonly
        self._exists = exists
        self._value = value
        self._set_value = set_value
        self._remove = remove

    # definition: el.AttributeDef
    # exists: bool
    # value: str | None


class EventEditor:
    """Allow to add/edit events of an HTML element according to its EventDef.
    The removal of events is not supported."""

    @property
    def handled(self) -> bool:
        return self._handled

    @property
    def definition(self) -> el.EventDef:
        return self._definition

    @property
    def method(self) -> code_info.Method | None:
        return self._method

    def do_action(self) -> None:
        """If the class does not have the method, add it.
        In any case it should focus the IDE cursor on the method.
        """
        self._do_action(self)

    def __init__(self, event_def: el.EventDef, method: code_info.Method | None, method_name: str,
                 _do_action: Callable[[EventEditor], None]):
        self._handled = method is not None
        self._method = method
        self._definition = event_def
        self.method_name = method_name
        self._do_action = _do_action


class ElementEditor:
    """Allow to edit an HTML element inside a Component, according to the specified ElementDef.
    Notice that the changes applied by an instance of this class  are not reflected in the internal state;
    it is expected that the hot reload will be triggered and consequently this instance will be discarded and
    reloaded.
    """

    def __init__(self, element_path: ep.ElementPath, element_def: el.ElementDef):
        self.attributes: ListMap[AttributeEditor] = ListMap(key_func=lambda attr: attr.definition.name)
        """One AttributeEditor for each attribute defined in the ElementDef."""
        self.events: ListMap[EventEditor] = ListMap(key_func=lambda ev: ev.definition.name)
        """One EventEditor for each event defined in the ElementDef."""

        self.element_path = element_path
        self.element_def = element_def
        self._fill_events()
        self._fill_attrs()

    def _fill_events(self):
        element_def = self.element_def
        element_path = self.element_path
        ci = code_info.class_info(self.current_python_source(), element_path.class_name)
        data_name = element_path.data_name
        for event_def in element_def.events:
            method_name = f'{data_name}__{event_def.python_name}'
            method = ci.methods_by_name.get(method_name, None)
            event_editor = EventEditor(event_def, method, method_name, self._event_do_action)
            self.events.append(event_editor)

    def _fill_attrs(self):
        element_def = self.element_def
        element_path = self.element_path
        node = html_locator.locate_node(self._html_source(), element_path.path)

        ad_content_string = el.AttributeDef('content string', el.Help('This is the inner content of the tag', ''), )
        self.attributes.append(AttributeEditor(ad_content_string, False, node.content, None, None))

        attributes = node.attributes
        for attribute_def in element_def.attributes:
            exists = attribute_def.name in attributes
            value = attributes.get(attribute_def.name, None)
            attribute_editor = AttributeEditor(attribute_def, exists, value,
                                               self._attribute_set_value, self._attribute_remove)
            self.attributes.append(attribute_editor)

    def current_python_source(self):
        return self._python_source_path().read_text()

    def _python_source_path(self):
        path = modlib._find_module_path(self.element_path.class_module)
        if not path:
            raise ValueError(f'Cannot find module {self.element_path.class_module}')
        return path

    def _html_source(self):
        ps = self.current_python_source()
        html = code_strings.html_from_source(ps, self.element_path.class_name)
        return html

    def _event_do_action(self, event_editor: EventEditor):
        if event_editor.handled:
            return
        new_source = code_edit.add_method(self.current_python_source(), self.element_path.class_name,
                                          event_editor.method_name, 'event',
                                          f"logger.debug(f'{event_editor.method_name} %s', event)")
        self._write_source(new_source)

    def _write_source(self, new_source):
        self._python_source_path().write_text(new_source)

    def _attribute_change(self, html_manipulator: Callable[[str], str]):
        python_source = self.current_python_source()
        new_source = code_strings.html_string_edit(python_source, self.element_path.class_name, html_manipulator)
        self._write_source(new_source)

    def _attribute_set_value(self, attribute_editor: AttributeEditor, value: str | None):

        def _html_manipulate(html: str) -> str:
            new_html = html_edit.html_attribute_set(
                html, self.element_path.path, attribute_editor.definition.name, value)
            return new_html

        self._attribute_change(_html_manipulate)

    def _attribute_remove(self, attribute_editor: AttributeEditor):

        def _html_manipulate(html: str) -> str:
            new_html = html_edit.html_attribute_remove(
                html, self.element_path.path, attribute_editor.definition.name)
            return new_html

        self._attribute_change(_html_manipulate)
