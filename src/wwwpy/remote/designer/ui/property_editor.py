from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.common import state, property_monitor
from wwwpy.common.designer import element_library, html_locator, code_strings
from wwwpy.common.designer.element_editor import ElementEditor, EventEditor
from wwwpy.common.designer.locator_lib import Locator, Origin
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.helpers import _element_path_lbl, _rpc_save, _log_event, _help_button
from .button_tab import ButtonTab, Tab
from .help_icon import HelpIcon
from .searchable_combobox2 import SearchableComboBox, Option


# write enum class with [events, attributes] and use it in the button click event
class PETab(str, Enum):
    """Property Editor Tab"""
    palette = 'palette'
    attributes = 'attributes'
    events = 'events'


@dataclass
class PropertyEditorState:
    mode: PETab = PETab.attributes


class PropertyEditor(wpc.Component, tag_name='wwwpy-property-editor'):
    row_container: js.HTMLElement = wpc.element()
    message1div: js.HTMLElement = wpc.element()
    _tabs: ButtonTab = wpc.element()
    _selected_element_path: Optional[Locator] = None
    state: PropertyEditorState = PropertyEditorState()

    @property
    def selected_element_path(self) -> Optional[Locator]:
        return self._selected_element_path

    @selected_element_path.setter
    def selected_element_path(self, value: Optional[Locator]):
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
            color: #e0e0e0;
            font-family: Arial, sans-serif;
        }
        .wwwpy-pe-box-padding {
            padding: 3px;
        }
        .wwwpy-pe-event-value {
             width: 90%;
            margin: 2px 0;
            padding: 5px;
            background-color: #2a2a2a;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 4px;
            font-size: 14px;
        }
    </style>
    <div>
<div data-name="message1div" style='color: white; margin: 0.3em'>&nbsp</div>
<wwwpy-button-tab data-name="_tabs"></wwwpy-button-tab>
<div  data-name='row_container' class="wwwpy-property-editor"></div>
</div>

        """

        def set_state_render(mode: PETab):
            self.state.mode = mode
            self._render()

        def new_tab(petab: PETab):
            return Tab(petab.name, on_selected=lambda tab: set_state_render(petab))

        self._tab_palette = new_tab(PETab.palette)
        self._tab_attributes = new_tab(PETab.attributes)
        self._tab_events = new_tab(PETab.events)
        self._tabs.tabs = [self._tab_palette, self._tab_attributes, self._tab_events, ]

    def set_state_selection_active(self):
        if self.state.mode == PETab.palette:
            self.state.mode = PETab.attributes

    def add_row(self, row: wpc.Component):
        row.element.classList.add('wwwpy-property-editor-row')
        self.row_container.appendChild(row.element)

    def _render(self):
        ep = self._selected_element_path
        # this is done here (and not in the moment of saving the ep) because
        # the stored ep could change in any moment, for example the user
        # change the type of tag from sl-button to sl-switch
        ep = _rebase_element_path_to_origin_source(ep)
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
        if self.state.mode == PETab.attributes:
            self._render_attribute_editor(element_def, ep)
            self._tab_attributes.selected = True
        elif self.state.mode == PETab.events:
            self._render_event_editor(element_def, ep)
            self._tab_events.selected = True
        else:
            self._tab_palette.selected = True

    def _set_title(self, lbl, value):
        pe_title = PE_title_row()
        pe_title.label.innerHTML = lbl
        pe_title.value.innerHTML = value
        self.add_row(pe_title)

    def _render_attribute_editor(self, element_def, ep):
        self._set_title('Attribute', 'Value')
        element_editor = ElementEditor(ep, element_def)
        for attr_editor in element_editor.attributes:
            attr_def = attr_editor.definition
            row1 = PE_attribute() if not attr_def.boolean else PE_attribute_bool()
            self.add_row(row1)

            row1.label.label.innerHTML = attr_def.name
            row1.label.set_help(attr_def.help)

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
            row1 = PE_event()
            self.add_row(row1)
            row1.label.label.innerHTML = event_editor.definition.name
            row1.label.set_help(event_editor.definition.help)
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

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        <slot name="label" data-name="label"></slot>
        <slot name="value" data-name="value"></slot>
            """


class PE_label(wpc.Component, tag_name='wwwpy-pe-label'):
    label: js.HTMLElement = wpc.element()
    _help: HelpIcon = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div style="width: 100%; display: flex; justify-content: space-between;">
            <span data-name="label"></span>
            <wwwpy-help-icon data-name="_help"></wwwpy-help-icon>
        </div>
            """

    def set_help(self, help: element_library.Help):
        self._help.href = help.url
        self._help.visible = help.url != ''


class PE_event(wpc.Component):
    label: PE_label = wpc.element()
    value: js.HTMLInputElement = wpc.element()
    double_click_handler = None

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <wwwpy-pe-label data-name="label"></wwwpy-pe-label> 
        <div>
            <input data-name='value' type="text" class="wwwpy-pe-box-padding wwwpy-pe-event-value">
        </div>
            """

    def value__dblclick(self, event):
        if self.double_click_handler:
            self.double_click_handler()


class PE_attribute(wpc.Component):
    label: PE_label = wpc.element()
    value: SearchableComboBox = wpc.element()
    double_click_handler = None

    def init_component(self):
        # language=html
        self.element.innerHTML = """       
        <wwwpy-pe-label data-name="label"></wwwpy-pe-label>        
        <wwwpy-searchable-combobox2 data-name='value' class="wwwpy-pe-box-padding"></wwwpy-searchable-combobox2>
            """

    def value__dblclick(self, event):
        if self.double_click_handler:
            self.double_click_handler()


class PE_attribute_bool(wpc.Component):
    label: PE_label = wpc.element()
    value: js.HTMLInputElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <wwwpy-pe-label data-name="label"></wwwpy-pe-label>
        <div>
            <input type="checkbox" data-name="value" style="transform: scale(1.4)">
        </div>
            """


class PE_title_row(wpc.Component):
    label: js.HTMLElement = wpc.element()
    value: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div style='font-weight: bold' data-name="label">Event</div><div style='font-weight: bold' data-name='value'>Value</div></div>        
            """


def _rebase_element_path_to_origin_source(ep: Locator) -> Optional[Locator]:
    """This is similar to rebase_path dumb because we use indexes alone.
    This rebase from Origin.live to Origin.source
    """
    if not ep:
        return None
    if ep.origin == Origin.source:
        return ep

    html = code_strings.html_from(ep.class_module, ep.class_name)
    if not html:
        return ep

    cst_node = html_locator.locate_node(html, ep.path)
    if cst_node is None:
        return ep

    node_path = html_locator.node_path_from_leaf(cst_node)
    ep_source = Locator(ep.class_module, ep.class_name, node_path, Origin.source)
    return ep_source
