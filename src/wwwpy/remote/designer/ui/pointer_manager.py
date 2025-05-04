from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Generic, TypeVar, Callable, Protocol

import js

from wwwpy.remote.designer.ui.pointer_api import PointerApi, PointerDown, PointerMove, PointerUp
from wwwpy.remote.designer.ui.type_listener import TypeListeners, DictListeners

logger = logging.getLogger(__name__)


@dataclass
class PMEvent: ...


@dataclass
class PMJsEvent(PMEvent):
    js_event: js.PointerEvent


TPE = TypeVar('TPE', bound=PMEvent)


@dataclass
class IdentifyEvent(PMJsEvent):
    action = None

    def set_action(self, action):
        self.action = action

    @property
    def is_action(self) -> bool:
        return self.action is not None

    def __str__(self):
        act = '' if self.is_action is None else f', action={self.action}'
        return f'IdentifyEvent(is_action={self.is_action}{act})'


@dataclass
class DeselectEvent(PMJsEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True


@dataclass
class HoverEvent(PMJsEvent):
    pass


class HasSelected(Protocol):
    selected: bool


THasSelected = TypeVar("THasSelected", bound=HasSelected)


@dataclass
class ActionChangedEvent(PMEvent):
    old: THasSelected | None
    new: THasSelected | None


class PointerManager(Generic[THasSelected]):
    def __init__(self) -> None:
        self._selected_action: THasSelected | None = None
        self.on_events: Callable[[PMEvent], None] = lambda ev: None
        self._listeners = DictListeners()
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

    def on(self, event_type: type[TPE]) -> TypeListeners[TPE]:
        return self._listeners.on(event_type)

    def _notify(self, ev: PMEvent) -> None:
        self._listeners.notify(ev)
        self.on_events(ev)

    def _toggle_selection(self, item: THasSelected):
        if item == self.selected_action:
            self.selected_action = None
        else:
            self.selected_action = item

    def _on_pointer_down(self, event: PointerDown):
        ie = IdentifyEvent(event.js_event)
        self._notify(ie)
        logger.debug(f'_on_pointer_down {ie} state={self.drag_state}')
        if ie.is_action:
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
        logger.debug(f'_on_pointer_move {ie} state={self.drag_state} '
                     f'ready_item={self._ready_item} drag_started={event.drag_started}')
        if event.drag_started and self._ready_item is not None:
            self.selected_action = self._ready_item
            self._ready_item = None

        if ie.is_action:
            return

        self._notify(HoverEvent(event.js_event))

    def _on_pointer_up(self, event: PointerUp):
        ie = IdentifyEvent(event.js_event)
        self._notify(ie)
        logger.debug(f'_on_pointer_up {ie} state={self.drag_state} ready_item={self._ready_item}')

        if event.stopped: ...

        ready = self._ready_item
        self._ready_item = None

        if event.normal_click and ie.is_action and ready is not None:
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
    def selected_action(self, new: THasSelected | None) -> None:
        msg = ''
        if self._ready_item:
            msg += f' ri={self._ready_item}'

        old = self.selected_action
        if old:
            old.selected = False
            msg += f' (deselecting {old})'
        if old != new:
            self._selected_action = new
            msg += f' (selecting {None if new is None else new})'
            if new:
                new.selected = True
            self._notify(ActionChangedEvent(old, new))

        logger.debug(msg)


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
