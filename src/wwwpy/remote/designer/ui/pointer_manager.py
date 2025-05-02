from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Literal, Protocol

import js

from wwwpy.remote.designer.ui.pointer_api import PointerApi, PointerDown, PointerMove, PointerUp
from wwwpy.remote.designer.ui.type_listener import TypeListeners

logger = logging.getLogger(__name__)


@dataclass
class PMEvent:
    js_event: js.PointerEvent


TPE = TypeVar('TPE', bound=PMEvent)


@dataclass
class IdentifyEvent(PMEvent):
    identified_as: Literal['action', 'canvas'] | None = None
    action = None


@dataclass
class DeselectEvent(PMEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True


@dataclass
class HoverEvent(PMEvent):
    pass


class HasSelected(Protocol):
    selected: bool


THasSelected = TypeVar("THasSelected", bound=HasSelected)


class PointerManager(Generic[THasSelected]):
    def __init__(self) -> None:
        self._selected_action: THasSelected | None = None
        self.on_events: Callable[[PMEvent], None] = lambda ev: None
        self._listeners: dict[type[PMEvent], TypeListeners] = {}
        self._ready_item: THasSelected | None = None

        self._pointer_api = PointerApi()
        self._pointer_api.on(PointerDown).add(self._on_pointer_down)
        self._pointer_api.on(PointerMove).add(self._on_pointer_move)
        self._pointer_api.on(PointerUp).add(self._on_pointer_up)

    def install(self) -> None:
        self._pointer_api.install()

    def uninstall(self) -> None:
        self._pointer_api.uninstall()

    @property
    def drag_state(self) -> str:
        return self._pointer_api.drag_state

    def listeners_for(self, event_type: type[TPE]) -> TypeListeners[TPE]:
        lst = self._listeners.get(event_type)
        if lst is None:
            lst = TypeListeners(event_type)
            self._listeners[event_type] = lst
        return lst

    def _notify(self, ev: PMEvent) -> None:
        listeners = self.listeners_for(type(ev))
        if listeners:
            listeners.notify(ev)
        self.on_events(ev)

    def _toggle_selection(self, item: THasSelected):
        if item == self.selected_action:
            self.selected_action = None
        else:
            self.selected_action = item

    def _on_pointer_down(self, event: PointerDown):
        ie = IdentifyEvent(event.js_event)
        self._notify(ie)
        logger.debug(f'_on_pointer_down state={self.drag_state} ie={ie.identified_as}')
        if ie.identified_as == 'action':
            self._ready_item = ie.action
            event.start_drag()
        else:
            ae = DeselectEvent(event.js_event)
            self._notify(ae)
            if ae.accepted:
                if self._selected_action is not None:
                    event.stop()
                self.selected_action = None

    def _on_pointer_move(self, event: PointerMove):
        ie = IdentifyEvent(event.js_event)
        self._notify(ie)
        logger.debug(f'_on_pointer_move ident_as={ie.identified_as} state={self.drag_state} '
                     f'ready_item={self._ready_item} drag_started={event.drag_started} ie={ie.identified_as}')
        if event.drag_started and self._ready_item is not None:
            self.selected_action = self._ready_item
            self._ready_item = None

        if ie.identified_as == 'action':
            return

        self._notify(HoverEvent(event.js_event))

    def _on_pointer_up(self, event: PointerUp):
        ie = IdentifyEvent(event.js_event)
        self._notify(ie)
        logger.debug(f'_on_pointer_up state={self.drag_state} ready_item={self._ready_item} ie={ie.identified_as}')

        if event.stopped: ...

        ready = self._ready_item
        self._ready_item = None

        if event.normal_click and ie.identified_as == 'action' and ready is not None:
            self._toggle_selection(ready)

        if event.drag_ended:
            ae = DeselectEvent(event.js_event)
            self._notify(ae)
            if ae.accepted:
                self.selected_action = None

    @property
    def selected_action(self) -> THasSelected | None:
        return self._selected_action

    @selected_action.setter
    def selected_action(self, value: THasSelected | None) -> None:
        msg = ''
        if self._ready_item:
            msg += f' ri={self._ready_item}'

        sel = self.selected_action
        if sel:
            sel.selected = False
            msg += f' (deselecting {sel})'

        self._selected_action = value
        msg += f' (selecting {None if value is None else value})'
        if value:
            value.selected = True

        logger.debug(msg)


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
