from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Callable, Literal

import js

import wwwpy.remote.eventlib as eventlib
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.eventlib import handler_options

logger = logging.getLogger(__name__)


@dataclass
class PMEvent:
    js_event: js.Event


_PE = TypeVar('_PE', bound=PMEvent)


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


class TypeListeners(Generic[_PE], list[Callable[[_PE], None]]):
    def __init__(self, event_type: type[_PE]) -> None:
        super().__init__()
        self.event_type = event_type

    def add(self, handler: Callable[[_PE], None]) -> None:
        self.append(handler)

    def remove(self, handler: Callable[[_PE], None]) -> None:
        super().remove(handler)

    def notify(self, event: _PE) -> None:
        if not isinstance(event, self.event_type):
            raise TypeError(f'Handler expects {self.event_type}')
        for h in list(self):
            h(event)


# todo resolve inconsistency where T is required to have property 'selected'
T = TypeVar('T')

class PointerManager(Generic[T]):
    def __init__(self) -> None:
        self._selected_action: Optional[T] = None
        self.on_events: Callable[[PMEvent], None] = lambda ev: None
        self._listeners: dict[type[PMEvent], TypeListeners] = {}
        self._drag_fsm = DragFsm()
        self._ready_item: Optional[T] = None
        self._stopped = False
        self._stop_next_click = False

    def install(self) -> None:
        eventlib.add_event_listeners(self)

    def uninstall(self) -> None:
        eventlib.remove_event_listeners(self)

    @property
    def drag_state(self) -> str:
        return self._drag_fsm.state

    def listeners_for(self, event_type: type[_PE]) -> TypeListeners[_PE]:
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

    def _stop(self, e: js.Event):
        e.stopPropagation()
        e.preventDefault()
        e.stopImmediatePropagation()

    def _toggle_selection(self, item: T):
        if item == self.selected_action:
            self.selected_action = None
        else:
            self.selected_action = item

    @handler_options(capture=True)
    def _js_window__click(self, event: js.MouseEvent):
        logger.debug(
            f'_js_window__click _stop_next_click={self._stop_next_click} _stopped={self._stopped} state={self._drag_fsm.state} ready_item={self._ready_item}')
        if self._stop_next_click:
            self._stop(event)
        self._stop_next_click = False

    @handler_options(capture=True)
    def _js_window__pointerdown(self, event: js.PointerEvent):
        ie = IdentifyEvent(event)
        self._notify(ie)
        logger.debug(f'_js_window__pointerdown state={self._drag_fsm.state} ie={ie.identified_as}')
        if ie.identified_as == 'action':
            self._ready_item = ie.action
            self._drag_fsm.pointerdown_accepted(event)
        else:
            ae = DeselectEvent(event)
            self._notify(ae)
            if ae.accepted:
                if self._selected_action is not None:
                    self._stop(event)
                    self._stopped = True
                    self._stop_next_click = True
                self.selected_action = None

    def _js_window__pointermove(self, event: js.PointerEvent):
        ie = IdentifyEvent(event)
        self._notify(ie)

        dragging = self._drag_fsm.transitioned_to_dragging(event)
        logger.debug(
            f'_js_window__pointermove ident_as={ie.identified_as} state={self._drag_fsm.state} ready_item={self._ready_item} dragging={dragging} ie={ie.identified_as}')
        if dragging and self._ready_item is not None:
            self.selected_action = self._ready_item
            self._ready_item = None

        if ie.identified_as == 'action':
            return

        he = HoverEvent(event)
        self._notify(he)

    @handler_options(capture=True)
    def _js_window__pointerup(self, event: js.PointerEvent):
        ie = IdentifyEvent(event)
        self._notify(ie)
        logger.debug(
            f'_js_window__pointerup _stopped={self._stopped} state={self._drag_fsm.state} ready_item={self._ready_item} ie={ie.identified_as}')

        if self._stopped:
            self._stop(event)
            self._stopped = False

        ready = self._ready_item
        self._ready_item = None

        if self._drag_fsm.state == DragFsm.READY and ie.identified_as == 'action' and ready is not None:
            self._toggle_selection(ready)

        if self._drag_fsm.state == DragFsm.DRAGGING:
            ae = DeselectEvent(event)
            self._notify(ae)
            if ae.accepted:
                self.selected_action = None

        self._drag_fsm.pointerup(event)

    @property
    def selected_action(self) -> Optional[T]:
        return self._selected_action

    @selected_action.setter
    def selected_action(self, action: Optional[T]) -> None:
        old = self._selected_action
        if old is not None and getattr(old, 'selected', False):
            old.selected = False
        self._selected_action = action
        if action is not None and getattr(action, 'selected', False) is False:
            action.selected = True
        logger.debug(f'PointerManager.selected_action → {action}')


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
