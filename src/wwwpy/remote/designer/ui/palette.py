from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js, eventlib, dict_to_py
from wwwpy.remote.component import get_component
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.eventlib import handler_options
from wwwpy.remote.jslib import get_deepest_element

logger = logging.getLogger(__name__)


class ActionItem:
    key: any
    """Unique object to identify the item in the palette."""

    label: str
    """Label to be displayed in the palette item."""

    selected: bool
    """True if the item is selected, False otherwise."""


class PaletteItem(ActionItem):

    @property
    def element(self) -> js.HTMLElement:
        """Return the element to be displayed in the palette item."""
        raise NotImplemented()


class Palette:
    selected_item: PaletteItem | None


class PaletteComponent(wpc.Component, Palette, tag_name='wwwpy-palette'):
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
        self.action_manager = ActionManager()
        self.action_manager.register(self)

    def connectedCallback(self):
        self.action_manager.install()

    def disconnectedCallback(self):
        self.action_manager.uninstall()

    def add_item(self, key: any, label: str) -> PaletteItemComponent:
        """Add an item to the palette."""
        item = PaletteItemComponent()
        item.key = key
        item.label = label
        item.element.classList.add('palette-item')
        self._item_container.appendChild(item.element)
        # item.element.addEventListener('click', create_proxy(lambda e: self.action_manager._action_item_click(item)))
        return item


class PaletteItemComponent(wpc.Component, PaletteItem, tag_name='palette-item-icon'):
    _label: js.HTMLLabelElement = wpc.element()

    # override magic method so the f strings get a nice representation
    def __repr__(self):
        return f'{self.__class__.__name__}({self.key}, {self.label})'

    def init_component(self):
        # language=html
        self.element.innerHTML = """
 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round"
      stroke-linejoin="round">
     <rect x="3" y="8" width="18" height="8" rx="2" ry="2"></rect>
     <line x1="12" y1="12" x2="12" y2="12"></line>
 </svg>
 <label data-name="_label"></label>
 </div>
 </div> 
"""
        self.key = None

    @property
    def label(self) -> str:
        return self._label.innerText

    @label.setter
    def label(self, value: str):
        self._label.innerText = value

    @property
    def selected(self) -> bool:
        return self.element.classList.contains('selected')

    @selected.setter
    def selected(self, value: bool):
        if value:
            self.element.classList.add('selected')
        else:
            self.element.classList.remove('selected')


@dataclass
class PaletteEvent:
    js_event: js.Event


_PE = TypeVar('_PE', bound=PaletteEvent)


@dataclass
class AcceptEvent(PaletteEvent):
    accepted: bool = False
    """Flag to indicate if the action has been spent/used"""

    def accept(self):
        self.accepted = True


@dataclass
class HoverEvent(PaletteEvent):
    pass


@dataclass
class DropEvent(PaletteEvent):
    source_element: js.HTMLElement | None = None
    target_element: js.HTMLElement | None = None


PaletteEventHandler = Callable[[_PE], None]


class TypeListeners(list[PaletteEventHandler]):
    """A list of event handlers for a specific event type."""

    def __init__(self, event_type: type[_PE]):
        super().__init__()
        self.event_type = event_type

    def add(self, handler: PaletteEventHandler):
        self.append(handler)

    def remove(self, handler: PaletteEventHandler):
        self.remove(handler)

    def notify(self, event: _PE):
        """Notify all listeners of the event."""
        if not isinstance(event, self.event_type):
            raise TypeError(f'Handler must be of type {self.event_type}')

        for handler in self:
            handler(event)


class ActionManager:
    """A class to manage interaction and events to handle, drag & drop, element selection, move element."""

    def __init__(self):
        self._selected_action: ActionItem | None = None
        self.on_events: PaletteEventHandler = lambda ev: None
        self._listeners = dict[type[_PE], list[PaletteEventHandler]]()
        self._drag_fsm = DragFsm()
        self._ready_item = None
        self._stopped = False
        self._stop_next_click = False  # new flag to also suppress the subsequent click

    def install(self):
        eventlib.add_event_listeners(self)

    def uninstall(self):
        eventlib.remove_event_listeners(self)

    @property
    def drag_state(self):
        return self._drag_fsm.state

    @handler_options(capture=True)
    def _js_window__click(self, event):
        if not self._in_palette(event) and self._stop_next_click:
            self._stop(event)
        self._stop_next_click = False

    @handler_options(capture=True)
    def _js_window__pointerdown(self, event):
        palette_item = _find_palette_item(event)
        logger.debug(
            f'_js_window__pointerdown {self._fsm_state()} pi={_pretty(palette_item)} event={dict_to_py(event)}')
        if palette_item:
            self._ready_item = palette_item
            self._drag_fsm.pointerdown_accepted(event)
        else:
            gesture_event = AcceptEvent(event)
            self._notify(gesture_event)
            if gesture_event.accepted:
                if self.selected_action is not None:
                    self._stop(event)
                    self._stopped = True
                    self._stop_next_click = True  # flag the next click for suppression
                self.selected_action = None

    def _js_window__pointermove(self, event):
        palette_item = _find_palette_item(event)
        dragging = self._drag_fsm.transitioned_to_dragging(event)

        msg = f'_js_window__pointermove {self._fsm_state()} pi={_pretty(palette_item)} ri={_pretty(self._ready_item)} dragging={dragging} event={dict_to_py(event)}'
        logger.debug(msg)

        if dragging:
            self.selected_action = self._ready_item
            self._ready_item = None

        if palette_item:
            return

        hover_event = HoverEvent(event)
        self._notify(hover_event)
        logger.debug(f'_js_window__pointermove hover_event: {hover_event}')

    @handler_options(capture=True)
    def _js_window__pointerup(self, event):
        logger.debug(f'_js_window__pointerup _stopped={self._stopped} event={dict_to_py(event)}')
        if self._stopped:
            self._stop(event)
            self._stopped = False
        self._ready_item = None
        if self._drag_fsm.state == DragFsm.READY:
            # If the drag was not accepted, we can assume it was a click
            palette_item = _find_palette_item(event)
            if palette_item:
                self._toggle_selection(palette_item)
        if self._drag_fsm.state == DragFsm.DRAGGING:
            gesture_event = AcceptEvent(event)
            self._notify(gesture_event)
            if gesture_event.accepted:
                self.selected_action = None
        self._drag_fsm.pointerup(event)

    def _fsm_state(self) -> str:
        return f'fsm={self._drag_fsm.state}'

    def _notify(self, event: _PE):
        """Notify all listeners of the event."""
        listeners = self.listeners_for(type(event))
        if listeners:
            listeners.notify(event)
        self.on_events(event)

    def listeners_for(self, event_type: type[_PE]) -> TypeListeners[_PE]:
        res = self._listeners.get(event_type)
        if res is None:
            res = TypeListeners(event_type)
            self._listeners[event_type] = res
        return res

    def _in_palette(self, event: js.Event) -> bool:
        target = _element_from_js_event(event)
        return target.closest(PaletteComponent.component_metadata.tag_name) is not None
        # ptag = PaletteComponent.component_metadata.tag_name
        # logger.debug(f'target.tagName={target.tagName} ptag={ptag}')
        # is_pal = element.tagName.casefold() == ptag.casefold()
        # logger.debug(f'is in palette: {is_pal}')
        # return is_pal

    def _stop(self, event):
        event.stopPropagation()
        event.preventDefault()
        event.stopImmediatePropagation()

    def _in_canvas(self, event: js.Event) -> bool:
        return not self._in_palette(event)

    def register(self, palette: Palette):
        pass

    @property
    def selected_action(self) -> ActionItem | None:
        """Return the currently selected item."""
        return self._selected_action

    @selected_action.setter
    def selected_action(self, value: ActionItem | None):
        """Set the currently selected item."""
        msg = ''
        if self._ready_item:
            msg += f' ri={self._ready_item.label}'

        sel = self.selected_action
        if sel:
            sel.selected = False
            msg += f' (deselecting {sel.label})'

        self._selected_action = value
        msg += f' (selecting {None if value is None else value.label})'
        if value:
            value.selected = True

        logger.debug(msg)

    def _toggle_selection(self, item: ActionItem):
        logger.debug(f'Item clicked: {item}')
        if item == self.selected_action:
            self.selected_action = None
            return

        self.selected_action = item


def _find_palette_item(event: js.Event) -> PaletteItem | None:
    target = _element_from_js_event(event)
    if target is None:  # tests missing. It looks like it happens when the mouse exit the viewport or moves on the scrollbar
        return None
    # logger.debug(f'_find_palette_item target={_pretty(target)}')
    res = target.closest(PaletteItemComponent.component_metadata.tag_name)
    if res:
        return get_component(res)
    return None


def _element_from_js_event(event: js.Event) -> js.Element | None:
    return get_deepest_element(event.clientX, event.clientY)


# language=html
_css_styles = """<style>
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


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
