from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

import js
import wwwpy.remote.component as wpc
from pyodide.ffi import create_proxy
from wwwpy.common import state, property_monitor
from wwwpy.common.designer import element_library, html_locator, code_strings
from wwwpy.common.designer.element_editor import ElementEditor, EventEditor
from wwwpy.common.designer.element_path import ElementPath
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.helpers import _element_path_lbl, _rpc_save, _log_event, _help_button

from .button_tab import ButtonTab, Tab
from .searchable_combobox2 import SearchableComboBox, Option


# write enum class with [events, attributes] and use it in the button click event
class PropertyEditorMode(str, Enum):
    palette = 'palette'
    events = 'events'
    attributes = 'attributes'


@dataclass
class PropertyEditorState:
    mode: PropertyEditorMode = PropertyEditorMode.events


class PropertyEditor(wpc.Component, tag_name='wwwpy-property-editor'):
    row_container: js.HTMLElement = wpc.element()
    message1div: js.HTMLElement = wpc.element()
    _tabs: ButtonTab = wpc.element()
    _selected_element_path: Optional[ElementPath] = None
    state: PropertyEditorState = PropertyEditorState()

    @property
    def selected_element_path(self) -> Optional[ElementPath]:
        return self._selected_element_path

    @selected_element_path.setter
    def selected_element_path(self, value: Optional[ElementPath]):
        self._selected_element_path = value
        self._render()

    def init_component(self):
        self._state_manager = state.State(state.JsStorage(), 'wwwpy.toolbar.property-editor.state')
        self.state = self._state_manager.restore(PropertyEditorState).instance_or_default()
        property_monitor.monitor_changes(self.state, lambda *a: self._state_manager.save(self.state))

        # language=html
        self.element.innerHTML = """
<style>
        .wwwpy-property-editor {
            display: grid;
            grid-template-columns: 2fr 3fr;
            box-sizing: content-box;
        }
        .wwwpy-property-editor-row {
            display: contents;
        }
        .wwwpy-property-editor-row > :first-child {
            display: flex;
            align-items: center;
            padding-left: 5px;
        }
        .wwwpy-property-input {
            width: 100%;
            padding: 3px;
            box-sizing: border-box;
            /* border: 1px solid ; */                     
        }
    </style>
<div data-name="message1div" style='color: white'>&nbsp</div>
<wwwpy-button-tab data-name="_tabs"></wwwpy-button-tab>
<div class="wwwpy-property-editor" data-name='row_container'>    
    <div class='wwwpy-property-editor-row' style='font-weight: bold'><div >Event</div><div>Value</div></div>
</div>

        """

        def set_state_render(mode: PropertyEditorMode):
            self.state.mode = mode
            self._render()

        self._tab_palette = Tab('palette', on_selected=lambda tab: set_state_render(PropertyEditorMode.palette))
        self._tab_events = Tab('events', on_selected=lambda tab: set_state_render(PropertyEditorMode.events))
        self._tab_attributes = Tab('attributes', on_selected=lambda tab: set_state_render(PropertyEditorMode.attributes))
        self._tabs.tabs = [self._tab_palette, self._tab_events, self._tab_attributes, ]

        for lbl in ['data-name', 'name', 'type', 'value', 'form']:
            row1 = PropertyEditorRowAttribute2()
            row1.element.classList.add('wwwpy-property-editor-row')
            self.row_container.appendChild(row1.element)
            row1.label.innerHTML = lbl
            row1.value.placeholder = 'Double click creates handler'
            if lbl == 'type':
                row1.value.value = 'text'

    def set_state_selection_active(self):
        if self.state.mode == PropertyEditorMode.palette:
            self.state.mode = PropertyEditorMode.events

    def add_row(self, row: wpc.Component):
        row.element.classList.add('wwwpy-property-editor-row')
        self.row_container.appendChild(row.element)

    def _render(self):
        ep = self._selected_element_path
        self.message1div.innerHTML = '' if ep is None else f'Selection: {_element_path_lbl(ep)}'

        self.row_container.innerHTML = ''
        visible = 'hidden' if ep is None else 'visible'
        self._tab_events.root_element().style.visibility = visible
        self._tab_attributes.root_element().style.visibility = visible
        if not ep:
            self._tab_palette.selected = True
            return
        lib = element_library.element_library()
        element_def = lib.by_tag_name(ep.tag_name)
        if not element_def:
            self.message1div.innerHTML += '<br>No metadata found for editing.'
            return
        self.message1div.innerHTML = f'Selection: {_element_path_lbl(ep)} {_help_button(element_def)}'
        html = code_strings.html_from(ep.class_module, ep.class_name)
        if not html:
            self.message1div.innerHTML += '<br>No HTML found for editing.'
            return

        cst_node = html_locator.locate_node(html, ep.path)
        if cst_node is None:
            self.message1div.innerHTML += '<br>No element found in the HTML.'
            return

        self.row_container.innerHTML = ''
        if self.state.mode == PropertyEditorMode.attributes:
            self._render_attribute_editor(element_def, ep)
            self._tab_attributes.selected = True
        elif self.state.mode == PropertyEditorMode.events:
            self._render_event_editor(element_def, ep)
            self._tab_events.selected = True
        else:
            self._tab_palette.selected = True

    def _set_title(self, lbl, value):
        pe_title = PropertyEditorTitleRow()
        pe_title.label.innerHTML = lbl
        pe_title.value.innerHTML = value
        self.add_row(pe_title)

    def _render_attribute_editor(self, element_def, ep):
        self._set_title('Attribute', 'Value')
        element_editor = ElementEditor(ep, element_def)
        for attr_editor in element_editor.attributes:
            attr_def = attr_editor.definition
            row1 = PropertyEditorRowAttribute() if not attr_def.boolean else PropertyEditorRowBoolAttribute()
            self.add_row(row1)
            row1.label.innerHTML = attr_def.name
            if not attr_def.boolean:
                options: List[Option] = [Option(value) for value in attr_def.values]
                focus_search = len(options) > 0
                for option in options:
                    if option.text == '':
                        option.label = 'Set to empty string'
                        option.italic = True

                if attr_editor.exists:
                    if not attr_def.mandatory:
                        remove = Option('remove attribute')
                        remove.actions.set_input_value = False
                        remove.italic = True

                        def remove_selected(ae=attr_editor):
                            ae.remove()
                            self._save(element_editor)

                        remove.on_selected = remove_selected  # lambda ae=attr_editor: ae.remove()
                        options.insert(0, remove)
                click_for = 'Click for options...'
                if attr_def.boolean:
                    row1.value.placeholder = 'attribute present' if attr_editor.exists else click_for
                else:
                    pre_placeholder = 'Set to empty string. ' if attr_editor.exists and attr_editor.value == '' else ''
                    row1.value.placeholder = pre_placeholder + (click_for if len(options) > 0 else '')
                row1.value.option_popup.options = options
                row1.value.text_value = '' if attr_editor.value is None else attr_editor.value
                row1.value.option_popup.search_placeholder = 'Search options...'
                row1.value.focus_search_on_popup = focus_search

                def attr_changed(event, ae=attr_editor, row=row1):
                    js.console.log(f'attr_changed {ae.definition.name} {row.value.text_value}')
                    ae.value = row.value.text_value
                    self._save(element_editor)

                row1.value.element.addEventListener('wp-change', create_proxy(attr_changed))
            else:
                if attr_editor.exists:
                    row1.value.checked = True
                else:
                    row1.value.checked = False

                def attr_changed(event, ae=attr_editor, row=row1):
                    if row.value.checked:
                        ae.value = None  # beware, this is creating the attribute with no value
                    else:
                        ae.remove()
                    self._save(element_editor)

                row1.value.addEventListener('change', create_proxy(attr_changed))

    def _save(self, element_editor):
        source = element_editor.current_python_source()

        async def start_save():
            await _rpc_save(self._selected_element_path, source)

        asyncio.create_task(start_save())

    def _render_event_editor(self, element_def, ep):
        self._set_title('Event', 'Value')
        element_editor = ElementEditor(ep, element_def)
        for event_editor in element_editor.events:
            row1 = PropertyEditorRowAttribute2()
            self.add_row(row1)
            row1.label.innerHTML = event_editor.definition.name
            row1.value.placeholder = '' if event_editor.handled else 'Double click creates handler'
            row1.value.readOnly = True
            row1.value.value = event_editor.method.name if event_editor.handled else ''

            def dblclick(ev: EventEditor = event_editor):
                js.console.log(f'dblclick on {ev.definition.name}')
                handled = ev.handled
                ev.do_action()
                source = element_editor.current_python_source()

                async def start_save():
                    if not handled:
                        await _rpc_save(ep, source)
                    await _log_event(element_editor, ev)

                asyncio.create_task(start_save())

            row1.double_click_handler = lambda ev=event_editor: dblclick(ev)


class PropertyEditorRow(wpc.Component, tag_name='wwwpy-property-editor-row'):
    label: js.HTMLElement = wpc.element()
    value: js.HTMLElement = wpc.element()

    def root_element(self):
        return self.shadow

    def init_component(self):
        self.shadow = self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.shadow.innerHTML = """
        <slot name="label" data-name="label"></slot>
        <slot name="value" data-name="value"></slot>
            """


class PropertyEditorRowAttribute2(wpc.Component):
    label: js.HTMLElement = wpc.element()
    value: js.HTMLInputElement = wpc.element()
    double_click_handler = None

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div data-name="label">uff</div><input data-name='value' type="text" class="wwwpy-property-input">
            """

    def value__dblclick(self, event):
        if self.double_click_handler:
            self.double_click_handler()


class PropertyEditorRowAttribute(wpc.Component):
    label: js.HTMLElement = wpc.element()
    value: SearchableComboBox = wpc.element()
    double_click_handler = None

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div data-name="label">uff</div>
        <wwwpy-searchable-combobox2 data-name='value' class="wwwpy-property-input"></wwwpy-searchable-combobox2>
            """

    def value__dblclick(self, event):
        if self.double_click_handler:
            self.double_click_handler()


class PropertyEditorRowBoolAttribute(wpc.Component):
    label: js.HTMLElement = wpc.element()
    value: js.HTMLInputElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div data-name="label">uff</div>
        <input type="checkbox" data-name="value" style="transform: scale(1.4)">
            """


class PropertyEditorTitleRow(wpc.Component):
    label: js.HTMLElement = wpc.element()
    value: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div style='font-weight: bold' data-name="label">Event</div><div style='font-weight: bold' data-name='value'>Value</div></div>        
            """
