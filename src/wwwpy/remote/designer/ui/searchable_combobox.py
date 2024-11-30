from __future__ import annotations

from dataclasses import dataclass
from typing import List, Union

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.global_interceptor import InterceptorEvent, GlobalInterceptor


@dataclass
class Actions:
    set_input_value = True
    hide_dropdown = True
    dispatch_change_event = True


class Option:
    parent: SearchableComboBox

    def __init__(self, text: str = ''):
        self.text = text
        self.actions = Actions()
        self.on_selected = lambda: None

    def _on_click(self, event: js.MouseEvent):
        js.console.log('_on_click', self.text)
        if self.actions.set_input_value:
            self.set_input_value()
        if self.actions.hide_dropdown:
            self.hide_dropdown()
        if self.actions.dispatch_change_event:
            self.dispatch_change_event()

        self.on_selected()

    def set_input_value(self):
        self.parent.input.value = self.text

    def hide_dropdown(self):
        self.parent.hide_dropdown()

    def dispatch_change_event(self):
        self.parent._dispatch_change_event()

    def create_element(self) -> js.HTMLElement:
        element = self.new_element()
        element.addEventListener('click', create_proxy(self._on_click))
        return element

    def new_element(self) -> js.HTMLElement:
        div: js.HTMLDivElement = js.document.createElement('div')
        div.textContent = self.text
        return div


class SearchableComboBox(wpc.Component, tag_name='wwwpy-searchable-combobox'):
    input: js.HTMLInputElement = wpc.element()
    search: js.HTMLInputElement = wpc.element()
    dropdown: js.HTMLElement = wpc.element()
    popup: js.HTMLElement = wpc.element()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        <style>
    :host {
        display: inline-block;
        position: relative;
        font-family: Arial, sans-serif;
    }
    input {
        width: 90%;
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
        <input type="text" placeholder="" data-name="input">
        <div data-name="popup" class="popup">
            <input type="search" placeholder="Search..." data-name="search">
            <div class="dropdown" data-name="dropdown"></div>
        </div>
        """
        self._interceptor = GlobalInterceptor(self._global_click)
        self._options = []
        self._dirty = False
        self.hide_dropdown()

    def _global_click(self, event: InterceptorEvent):
        click_inside = self.element.contains(event.target)
        js.console.log(f'global click: contains={click_inside}', event.target)
        if click_inside:
            return
        self.hide_dropdown()

    def search__input(self, event):
        self.filter_options()

    def input__change(self, event):
        if self._is_free_edit():
            self._dispatch_change_event()

    def input__mousedown(self, event: js.MouseEvent):
        if self._is_free_edit():
            return
        event.preventDefault()

    @property
    def _search_visible(self):
        return self.popup.style.display != 'none'

    def input__click(self, event: js.MouseEvent):
        if self._search_visible:
            self.hide_dropdown()
        else:
            self.show_dropdown()

    def show_dropdown(self):
        if self._is_free_edit():
            return
        if self._dirty:
            self.filter_options()
        self.popup.style.display = 'block'
        self.search.focus()
        self._interceptor.install()

    def _is_free_edit(self):
        return not self._options

    def hide_dropdown(self):
        self.popup.style.display = 'none'
        self._interceptor.uninstall()

    def set_options(self, options: List[Union[str, Option]]):
        self._options = options
        self._dirty = True

    def filter_options(self, event=None):
        self._dirty = False
        filter_text = self.search.value.lower()
        self.dropdown.innerHTML = ''

        for option in self._options:
            if isinstance(option, str):
                option = Option(option)
            option.parent = self
            option: Option
            if filter_text in option.text.lower():
                self.dropdown.appendChild(option.create_element())

        if not self.dropdown.hasChildNodes():
            div: js.HTMLDivElement = js.document.createElement('div')
            div.textContent = 'No results'
            div.style.textAlign = 'center'
            div.style.fontStyle = 'italic'
            div.style.fontWeight = 'bold'
            div.style.pointerEvents = 'none'
            self.dropdown.appendChild(div)

    def select_option(self, option):
        js.console.log(f'option: {option}')
        self.input.value = option
        self.hide_dropdown()
        self._dispatch_change_event()

    def _dispatch_change_event(self):
        self.element.dispatchEvent(js.CustomEvent.new('wp-change', {'detail': self.input.value}))
