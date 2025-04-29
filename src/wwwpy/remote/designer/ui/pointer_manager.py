from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional, Callable, Literal

import js

import wwwpy.remote.eventlib as eventlib
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.eventlib import handler_options

logger = logging.getLogger(__name__)
T = TypeVar('T')


@dataclass
class PMEvent:
    js_event: js.Event


@dataclass
class IdentifyEvent(PMEvent):
    """User must set .identified_as to 'action' or 'canvas'"""
    identified_as: Literal['action', 'canvas'] | None = None


@dataclass
class AcceptEvent(PMEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True


@dataclass
class HoverEvent(PMEvent):
    pass


@dataclass
class DropEvent(PMEvent):
    source_item: Optional[T] = None
    target_element: Optional[js.Element] = None


class TypeListeners(list[Callable[[PMEvent], None]]):
    def __init__(self, event_type: type[PMEvent]):
        super().__init__()
        self.event_type = event_type

    def add(self, handler: Callable[[PMEvent], None]):
        self.append(handler)

    def remove(self, handler: Callable[[PMEvent], None]):
        super().remove(handler)

    def notify(self, event: PMEvent):
        if not isinstance(event, self.event_type):
            raise TypeError(f'Handler expects {self.event_type}')
        for h in list(self):
            h(event)


class PointerManager(Generic[T]):
    def __init__(self) -> None:
        self._selected_action: Optional[T] = None
        self.on_events: Callable[[PMEvent], None] = lambda ev: None
        self._listeners: dict[type[PMEvent], TypeListeners] = {}
        self._drag_fsm = DragFsm()
        self._ready: Optional[T] = None
        self._stopped = False
        self._stop_next_click = False
        # user must call register() to supply a finder from js.Event -> T|None
        self._find_item: Callable[[js.Event], Optional[T]] = lambda ev: None

    def install(self) -> None:
        eventlib.add_event_listeners(self)

    def uninstall(self) -> None:
        eventlib.remove_event_listeners(self)

    def register(self, finder: Callable[[js.Event], Optional[T]]) -> None:
        """Supply a function to map a raw js.Event to your ActionItem T (or None)."""
        self._find_item = finder

    @property
    def drag_state(self) -> str:
        return self._drag_fsm.state

    def listeners_for(self, event_type: type[PMEvent]) -> TypeListeners:
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
        if self._selected_action is not None and self._stop_next_click:
            self._stop(event)
        self._stop_next_click = False

    @handler_options(capture=True)
    def _js_window__pointerdown(self, event: js.PointerEvent):
        ie = IdentifyEvent(event)
        self._notify(ie)
        if ie.identified_as == 'action':
            self._ready = self._find_item(event)
            self._drag_fsm.pointerdown_accepted(event)
        else:
            ae = AcceptEvent(event)
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
        if dragging and self._ready is not None:
            self.selected_action = self._ready
            self._ready = None

        if ie.identified_as == 'action':
            return

        he = HoverEvent(event)
        self._notify(he)

    @handler_options(capture=True)
    def _js_window__pointerup(self, event: js.PointerEvent):
        ie = IdentifyEvent(event)
        self._notify(ie)

        if self._stopped:
            self._stop(event)
            self._stopped = False

        ready = self._ready
        self._ready = None

        if self._drag_fsm.state == DragFsm.READY and ie.identified_as == 'action' and ready is not None:
            self._toggle_selection(ready)

        if self._drag_fsm.state == DragFsm.DRAGGING:
            ae = AcceptEvent(event)
            self._notify(ae)
            if ae.accepted:
                self.selected_action = None
            de = DropEvent(event, source_item=ready, target_element=event.target)  # optional
            self._notify(de)

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
