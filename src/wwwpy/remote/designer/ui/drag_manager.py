from __future__ import annotations

import logging
from collections.abc import Callable

import js
from pyodide.ffi import create_proxy

from wwwpy.remote import eventlib

logger = logging.getLogger(__name__)


class DragFsm:
    IDLE = "IDLE"
    READY = "READY"
    DRAGGING = "DRAGGING"

    DRAG_THRESHOLD_PX = 5

    def __init__(self):
        self.state = self.IDLE
        self.drag_start = (-1, -1)

    def reset(self):
        self.state = self.IDLE
        self.drag_start = (-1, -1)

    def pointerdown_accepted(self, event):
        was = self.state
        if self.state == self.IDLE:
            # logger.debug(f"Pointer down on valid source")
            self.drag_start = (event.clientX, event.clientY)
            self.state = self.READY
            event.target.setPointerCapture(event.pointerId)
            event.preventDefault()
            # event.stopPropagation()
        logger.debug(f'pointerdown_accepted was={was} now={self.state}')

    def pointermove(self, event) -> str:
        was = self.state
        if self.state == self.READY:
            # Check if we've moved enough to consider this a drag
            dx = abs(event.clientX - self.drag_start[0])
            dy = abs(event.clientY - self.drag_start[1])

            if dx > self.DRAG_THRESHOLD_PX or dy > self.DRAG_THRESHOLD_PX:
                logger.debug("Drag threshold exceeded, entering DRAG_ACTIVE state")
                self.state = self.DRAGGING
        logger.debug(f'pointermove was={was} now={self.state}')
        return self.state

    def transitioned_to_dragging(self, event) -> bool:
        if self.state != self.READY:
            return False
        self.pointermove(event)
        return self.state == self.DRAGGING

    def pointerup(self, event):
        was = self.state
        self.reset()
        logger.debug(f'pointerup was={was} now={self.state}')


OnPointerDownAcceptType = Callable[[js.Event], bool]


class DragManager:
    """
    Manages pointer state and interactions (click or drag) between source and target elements.

    This class tracks the state of pointer interactions and emits events at appropriate times.
    It supports both click-based and drag-based interaction patterns.
    """

    def __init__(self, on_pointerdown_accept: OnPointerDownAcceptType | None = None):
        """Initialize the PointerManager with default state and callbacks."""
        self._fsm = DragFsm()

        # Event callbacks
        if on_pointerdown_accept is None:
            on_pointerdown_accept = lambda event: False  # Default rejects all

        self.on_pointerdown_accept: OnPointerDownAcceptType = on_pointerdown_accept

    def install(self):
        eventlib.add_event_listeners(self)

    def uninstall(self):
        eventlib.remove_event_listeners(self)

    @property
    def state(self):
        return self._fsm.state

    def _js_window__pointerdown(self, event):
        if self.on_pointerdown_accept(event):
            self._fsm.pointerdown_accepted(event)

    def _js_window__pointermove(self, event):
        """Handle pointer move events for dragging and hovering."""
        self._fsm.pointermove(event)

    def _js_window__pointerup(self, event):
        """Handle pointer up events to complete drag operations."""
        self._fsm.pointerup(event)
