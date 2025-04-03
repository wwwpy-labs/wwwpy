from __future__ import annotations

import logging

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js

logger = logging.getLogger(__name__)


class PaletteItem:
    key: any
    """Unique object to identify the item in the palette."""
    label: str
    """Label to be displayed in the palette item."""

    selected: bool
    """True if the item is selected, False otherwise."""

    @property
    def element(self) -> js.HTMLElement:
        """Return the element to be displayed in the palette item."""
        raise NotImplemented()


class PaletteItemComponent(wpc.Component, PaletteItem, tag_name='palette-item-icon'):
    _label: js.HTMLLabelElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="8" width="18" height="8" rx="2" ry="2"></rect>
                <line x1="12" y1="12" x2="12" y2="12"></line>
            </svg>
            <label data-name="_label"></label>
        """
        self.key = None

    @property
    def label(self) -> str:
        return self._label.innerText

    @label.setter
    def label(self, value: str):
        self._label.innerText = value


class PaletteComponent(wpc.Component, tag_name='wwwpy-palette'):

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        """
        self.selected_item: PaletteItem | None = None
        # self._items: List[PaletteItemComponent] = []

    # @property
    # def items(self) -> Tuple[PaletteItem, ...]:
    #     """Return the tuple of items in the palette."""
    #     # return self._items
    #     return tuple(self._items)

    def add_item(self, key: any, label: str) -> PaletteItem:
        """Add an item to the palette."""
        item = PaletteItemComponent()
        item.key = key
        item.label = label
        # self._items.append(item)
        self.element.shadowRoot.appendChild(item.element)
        item.element.addEventListener('click', create_proxy(lambda e: self._item_click(e, item)))
        return item

    def _item_click(self, e, item: PaletteItem):

        if item == self.selected_item:
            self._deselect()
            return

        self._deselect()

        self.selected_item = item
        item.selected = True

    def _deselect(self):
        sel = self.selected_item
        if sel:
            self.selected_item = None
            sel.selected = False


class GestureManager:
    """A class to manage interaction and events to handle, drag & drop, element selection, move element."""

    def install(self):
        """Install the gesture manager"""

    def uninstall(self):
        """Uninstall the gesture manager"""
