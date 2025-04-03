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


class PaletteComponent(wpc.Component, tag_name='wwwpy-palette'):
    _item_container: js.HTMLDivElement = wpc.element()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """        
    <div class="container">
        <div class="palette" data-name="_item_container">
        </div>
    </div>
        """
        self.element.shadowRoot.innerHTML += _css_styles
        self._selected_item: PaletteItem | None = None
        # self._items: List[PaletteItemComponent] = []

    @property
    def selected_item(self) -> PaletteItem | None:
        """Return the currently selected item."""
        return self._selected_item

    @selected_item.setter
    def selected_item(self, value: PaletteItem | None):
        """Set the currently selected item."""
        msg = ''
        sel = self.selected_item
        if sel:
            sel.selected = False
            msg += f' (deselecting {sel})'

        self._selected_item = value
        msg += f' (selecting {value})'
        if value:
            value.selected = True

        logger.debug(msg)

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
        item.element.classList.add('palette-item')
        # self._items.append(item)
        self._item_container.appendChild(item.element)
        item.element.addEventListener('click', create_proxy(lambda e: self._item_click(e, item)))
        return item

    def _item_click(self, e, item: PaletteItem):
        logger.debug(f'Item clicked: {item}')
        if item == self.selected_item:
            self.selected_item = None
            return

        self.selected_item = item
        item.selected = True


class PaletteItemComponent(wpc.Component, PaletteItem, tag_name='palette-item-icon'):
    _label: js.HTMLLabelElement = wpc.element()

    # override magic method so the f strings get a nice representation
    def __repr__(self):
        return f'{self.__class__.__name__}({self.key}, {self.label})'

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        
         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="8" width="18" height="8" rx="2" ry="2"></rect>
                <line x1="12" y1="12" x2="12" y2="12"></line>
            </svg>
            <label data-name="_label"></label>
        </div>
    </div>
        """
        self.key = None
        self._selected = False

    @property
    def label(self) -> str:
        return self._label.innerText

    @label.setter
    def label(self, value: str):
        self._label.innerText = value

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        self._selected = value
        if value:
            self.element.classList.add('selected')
        else:
            self.element.classList.remove('selected')


class GestureManager:
    """A class to manage interaction and events to handle, drag & drop, element selection, move element."""

    def install(self):
        """Install the gesture manager"""

    def uninstall(self):
        """Uninstall the gesture manager"""


# language=html
_css_styles = """
<style>
        :host {
            --primary-color: #6366f1;
            --primary-hover: #818cf8;
            --secondary-color: #4f46e5;
            --border-color: #4b5563;
            --shadow-color: rgba(0, 0, 0, 0.3);
            --workspace-bg: #1e1e2e;
            --palette-bg: #27293d;
            --text-color: #e2e8f0;
            --item-bg: #2d3748;
            --item-hover-bg: #3a4358;
            --selected-bg: #4c1d95;
            --selected-border: #8b5cf6;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            background-color: #111827;
            color: var(--text-color);
        }

        .header {
            background-color: var(--primary-color);
            color: white;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 5px var(--shadow-color);
        }

        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }

        .palette {
            width: 220px;
            background-color: var(--palette-bg);
            padding: 1rem;
            border-right: 1px solid var(--border-color);
            box-shadow: 2px 0 5px var(--shadow-color);
            overflow-y: auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            align-content: start;
            height: fit-content;
            max-height: 100%;
        }

        .workspace {
            flex: 1;
            background-color: var(--workspace-bg);
            padding: 2rem;
            overflow: auto;
            position: relative;
        }

        .palette-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            user-select: none;
            background-color: var(--item-bg);
            font-size: 12px;
            color: var(--text-color);
            touch-action: none;
        }

        .palette-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 3px 5px var(--shadow-color);
            background-color: var(--item-hover-bg);
        }

        .palette-item.selected {
            background-color: var(--selected-bg);
            border: 1px solid var(--selected-border);
            box-shadow: 0 0 0 2px var(--selected-border), 0 0 12px rgba(139, 92, 246, 0.5);
            position: relative;
            transform: scale(1.05);
        }

        .palette-item svg {
            margin-bottom: 8px;
            width: 36px;
            height: 36px;
        }

        .log-panel {
            padding: 1rem;
            background-color: #2c3e50;
            color: #ecf0f1;
            max-height: 150px;
            overflow-y: auto;
            font-family: monospace;
        }

        .log-entry {
            margin-bottom: 5px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 5px;
        }

        .log-entry:last-child {
            border-bottom: none;
        }

        /* Element previews in workspace */
        .element-preview {
            position: absolute;
            border: 2px dashed var(--primary-color);
            padding: 5px;
            border-radius: 4px;
            background-color: rgba(52, 152, 219, 0.1);
            min-width: 100px;
            min-height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: #666;
        }

        /* Dragging Element Preview */
        .dragging-element {
            position: absolute;
            pointer-events: none;
            opacity: 0.8;
            z-index: 1000;
            transform: translate(-50%, -50%);
            background-color: var(--selected-bg);
            border: 1px solid var(--selected-border);
            padding: 5px 10px;
            border-radius: 4px;
            color: white;
            font-size: 12px;
        }
    </style>
"""
