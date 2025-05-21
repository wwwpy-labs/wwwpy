import logging
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar

import js

from wwwpy.common.type_listener import TypeListeners, DictListeners
from wwwpy.remote import eventlib
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.eventlib import handler_options

logger = logging.getLogger(__name__)


@dataclass
class PAEvent:
    js_event: js.PointerEvent


TPA = TypeVar('TPA', bound=PAEvent)


@dataclass
class PointerDown(PAEvent):
    _stop = False
    _start_drag = False

    def stop(self):
        if self._start_drag:
            raise RuntimeError('Cannot stop, start_drag already set')
        self._stop = True

    def start_drag(self):
        if self._stop:
            raise RuntimeError('Cannot start drag, stop already set')
        self._start_drag = True


@dataclass
class PointerMove(PAEvent):
    drag_started: bool


class Reason(str, Enum):
    normal_click = 'NORMAL_CLICK'
    drag_ended = 'DRAG_ENDED'
    stopped = 'STOPPED'


@dataclass
class PointerUp(PAEvent):
    reason: Reason

    @property
    def stopped(self) -> bool:
        return self.reason == Reason.stopped

    @property
    def drag_ended(self) -> bool:
        return self.reason == Reason.drag_ended

    @property
    def normal_click(self) -> bool:
        return self.reason == Reason.normal_click


class PointerApi:
    def __init__(self) -> None:
        self._listeners = DictListeners()
        self._drag_fsm = DragFsm()
        self._stopped = False
        self._stop_next_click = False

    def install(self) -> None:
        eventlib.add_event_listeners(self)

    def uninstall(self) -> None:
        eventlib.remove_event_listeners(self)

    @property
    def drag_state(self) -> str:
        return self._drag_fsm.state

    def on(self, event_type: type[TPA]) -> TypeListeners[TPA]:
        return self._listeners.on(event_type)

    def _notify(self, ev: PAEvent) -> None:
        self._listeners.notify(ev)

    @handler_options(capture=True)
    def _js_window__click(self, event: js.MouseEvent):
        logger.debug(
            f'_js_window__click _stop_next_click={self._stop_next_click} _stopped={self._stopped} state={self._drag_fsm.state}')
        if self._stop_next_click:
            _stop_js_event(event)
        self._stop_next_click = False

    @handler_options(capture=True)
    def _js_window__pointerdown(self, event: js.PointerEvent):
        e = PointerDown(event)
        self._notify(e)
        if e._start_drag:
            self._drag_fsm.pointerdown_accepted(event)
        elif e._stop:
            _stop_js_event(event)
            self._stopped = True
            self._stop_next_click = True

    def _js_window__pointermove(self, event: js.PointerEvent):
        dragging = self._drag_fsm.transitioned_to_dragging(event)
        e = PointerMove(event, dragging)
        self._notify(e)

    @handler_options(capture=True)
    def _js_window__pointerup(self, event: js.PointerEvent):
        r = None
        if self._drag_fsm.state == DragFsm.DRAGGING:
            r = Reason.drag_ended
        elif self._drag_fsm.state == DragFsm.READY:
            r = Reason.normal_click
        elif self._stopped:
            r = Reason.stopped
            _stop_js_event(event)
            self._stopped = False

        self._drag_fsm.pointerup(event)
        if r:
            self._notify(PointerUp(event, r))
        else:
            logger.debug(f'_js_window__pointerup: no event to notify fsm={self._drag_fsm.state}')


def _stop_js_event(e: js.Event):
    e.stopPropagation()
    e.preventDefault()
    e.stopImmediatePropagation()


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
