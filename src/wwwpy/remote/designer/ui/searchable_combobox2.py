from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from wwwpy.remote.databind.bind_wrapper import InputTargetAdapter
from wwwpy.remote.designer.global_interceptor import InterceptorEvent, GlobalInterceptor


@dataclass
class Actions:
    set_input_value = True
    # hide_dropdown = True
    # dispatch_change_event = True


class Option:
    parent: SearchableComboBox

    def __init__(self, text: str = ''):
        self.text = text
        self.actions = Actions()
        self.on_selected = lambda: None
        self._root_element: js.HTMLElement = None

    @property
    def loaded(self) -> bool:
        return self._root_element is not None

    @property
    def label(self) -> str:
        return self.root_element().innerText

    @label.setter
    def label(self, value: str):
        self.root_element().innerText = value

    @property
    def italic(self) -> bool:
        return self.root_element().style.fontStyle == 'italic'

    @italic.setter
    def italic(self, value: bool):
        self.root_element().style.fontStyle = 'italic' if value else ''

    def root_element(self) -> js.HTMLElement:
        if self._root_element is None:
            div = js.document.createElement('div')
            div.textContent = self.text
            div.addEventListener('click', create_proxy(self.do_click))
            self._root_element = div
        return self._root_element

    def do_click(self, *event):
        self.parent._option_selected(self)
        self.on_selected()

    def update_visibility(self, search: str):
        self.visible = search.lower() in self.text.lower()

    @property
    def visible(self) -> bool:
        return not (self._root_element.style.display == 'none')

    @visible.setter
    def visible(self, value):
        self.root_element().style.display = 'block' if value else 'none'


class OptionPopup(wpc.Component, tag_name='wwwpy-searchable-combobox2-option-popup'):
    _options = []  # type: List[Option]
    parent: SearchableComboBox
    _root: js.HTMLElement = wpc.element()
    _search: js.HTMLInputElement = wpc.element()
    _dirty = True

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <div><input type="search" data-name="_search">
        <div data-name="_root" class="dropdown"></div>
        </div>
        """
        self._interceptor = GlobalInterceptor(self._global_click)

    def _global_click(self, event: InterceptorEvent):
        target = event.event.composedPath()[0]
        click_inside = self.parent.root_element().contains(target)
        js.console.log(f'global click: contains={click_inside}', target)
        if click_inside:
            return
        self.hide()

    @property
    def visible(self) -> bool:
        return self.element.style.display != 'none'

    @property
    def options(self) -> List[Option]:
        return self._options

    @options.setter
    def options(self, value: List[Union[str, Option]]):
        def process(v):
            if not isinstance(v, Option):
                v = Option(v)
            v.parent = self.parent
            return v

        self._options = [process(v) for v in value]
        self._dirty = True

    @property
    def search_placeholder(self) -> str:
        return self._search.placeholder

    @search_placeholder.setter
    def search_placeholder(self, value):
        self._search.placeholder = value

    @property
    def search_value(self):
        return self._search.value

    @search_value.setter
    def search_value(self, value: str):
        self._search.value = value
        self._update_options_vis()

    def _search__input(self, event):
        self._update_options_vis()

    def _update_options_vis(self):
        for option in self._options:
            option.update_visibility(self._search.value)

    def show(self):
        if self._dirty:
            self._dirty = False
            root = self._root
            root.innerHTML = ''
            for option in self._options:
                option.parent = self.parent
                root.append(option.root_element())

        self.element.style.display = 'block'
        self._interceptor.install()

    def hide(self):
        self.element.style.display = 'none'
        self._interceptor.uninstall()

    def focus_search(self):
        self._search.focus()


class SearchableComboBox(wpc.Component, tag_name='wwwpy-searchable-combobox2'):
    _input: js.HTMLInputElement = wpc.element()
    option_popup: OptionPopup = wpc.element()
    value: str | None = wpc.attribute()
    disabled: str | None = wpc.attribute()

    focus_search_on_popup = True
    """This represents the popoup with the options and eventually a search box at the top to filter the options"""

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>        
:host {
    display: block; /* Ensures the host element takes full width if needed */
    position: relative;
    font-family: Arial, sans-serif;
    width: 100%; /* Optional, only if the host should also span full width */
}

input {
    width: 100%; /* Makes the input take the full width of the host */
    box-sizing: border-box; /* Ensures padding and border are included in the width */
    padding: 5px;
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    font-size: 14px;
}
    input::placeholder {
        color: #888;
    }
    .dropdown {
        position: absolute;
        width: 100%;
        max-height: 200px;
        resize: both;
        overflow-y: auto;
        border: 1px solid #444;
        background-color: #333;
        color: #e0e0e0;
        border-radius: 0 0 4px 4px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .popup {
        position: absolute;
        z-index: 1000;
        display: none;
    }   
    .dropdown * {
        padding: 8px 12px;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    .dropdown div:hover {
        background-color: #444;
    }
    input:focus {
        outline: none;
        border-color: #666;
        box-shadow: 0 0 0 2px rgba(100, 100, 100, 0.3);
    }      
</style>
        <input data-name="_input">
        <wwwpy-searchable-combobox2-option-popup 
            data-name="option_popup" class="popup" style="display: none">
        </wwwpy-searchable-combobox2-option-popup>
        """
        self.target_adapter = InputTargetAdapter(self._input)
        self.option_popup.parent = self
        self.option_popup.search_placeholder = 'search...'
        self._update_attributes()

    def _update_attributes(self):
        if self.value is None:
            self.value = ''
        elif self.value != self._input.value:
            self._input.value = self.value

        if self.disabled is not None:
            self._input.disabled = True
        else:
            self._input.disabled = False

    def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
        self._update_attributes()

    @property
    def text_value(self) -> str:
        return self._input.value

    @text_value.setter
    def text_value(self, value: str):
        self._input.value = value

    @property
    def placeholder(self) -> str:
        return self._input.placeholder

    @placeholder.setter
    def placeholder(self, value: str):
        self._input.placeholder = value

    def _input_element(self) -> js.HTMLElement:
        return self._input

    def _input__pointerdown(self, event):
        if len(self.option_popup.options) == 0:
            self._input.focus()
            return
        vis = self.option_popup.visible
        if vis:
            self.option_popup.hide()
        else:
            self.option_popup.show()
            if self.focus_search_on_popup:
                self.option_popup.focus_search()
            else:
                self._input.focus()

    def _input__change(self, event):
        self.element.dispatchEvent(js.CustomEvent.new('wp-change'))
        self.target_adapter._new_input_event(None)

    def _option_selected(self, option: Option):
        self.option_popup.hide()
        if option.actions.set_input_value:
            print(f'option selected: {option.text}')
            self._input.value = option.text
            self.element.dispatchEvent(js.CustomEvent.new('wp-change', dict_to_js({'detail': {'option': option}})))
            self.target_adapter._new_input_event(None)

    def _input__input(self, event):
        self.target_adapter._new_input_event(event)
