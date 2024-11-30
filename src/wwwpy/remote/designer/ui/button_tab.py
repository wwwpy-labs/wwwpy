from __future__ import annotations

from typing import List, Union, Callable

import wwwpy.remote.component as wpc
import js
from wwwpy.remote import dict_to_js
from pyodide.ffi import create_proxy
import logging

logger = logging.getLogger(__name__)

class ButtonTab(wpc.Component, tag_name='wwwpy-button-tab'):
    _root: js.HTMLElement = wpc.element()

    @property
    def tabs(self) -> List[Tab]:
        return self._tabs

    @tabs.setter
    def tabs(self, value: List[Union[str, Tab]]):
        def process(v):
            if not isinstance(v, Tab):
                v = Tab(v)
            v.parent = self
            return v

        self._tabs = [process(v) for v in value]
        re = self._root
        re.innerHTML = ''
        for tab in self._tabs:
            re.appendChild(tab.root_element())

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>
  .selected {
        box-shadow: 0 0 0 2px darkgray;
        }
</style>
<span data-name="_root"></span>
"""
        style = self._root.style
        style.display = 'flex'
        style.justifyContent = 'space-around'
        style.width = '100%'

        self._tabs = []
        self._updating = False

    def _tab_selected(self, tab: Tab):
        if self._updating:
            return
        self._updating = True
        for t in self._tabs:
            t.selected = t == tab
        self._updating = False

_selected_default = lambda tab: None


class Tab:
    parent: ButtonTab

    def __init__(self, text: str = '', on_selected: Callable[[Tab], None] = _selected_default):
        self.text = text
        self.on_selected = on_selected
        self._root_element: js.HTMLElement = None

    def do_click(self, *event):
        self.selected = True
        self.on_selected(self)

    def root_element(self) -> js.HTMLElement:
        if self._root_element is None:
            div = js.document.createElement('button')
            div.textContent = self.text
            div.addEventListener('click', create_proxy(self.do_click))
            self._root_element = div
        return self._root_element

    @property
    def selected(self) -> bool:
        return self.root_element().classList.contains('selected')

    @selected.setter
    def selected(self, value: bool):
        current = self.selected
        class_list = self.root_element().classList
        if value:
            class_list.add('selected')
        else:
            class_list.remove('selected')

        self.parent._tab_selected(self)
