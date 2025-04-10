from __future__ import annotations

import logging

from pyodide.ffi import create_proxy

from wwwpy.remote import eventlib

logger = logging.getLogger(__name__)


class DragFsm:
    IDLE = "idle"
    READY = "ready"
    DRAGGING = "dragging"

    DRAG_THRESHOLD_PX = 5

    def __init__(self):
        self.state = self.IDLE
        self.drag_start = (-1, -1)

    def reset(self):
        self.state = self.IDLE
        self.drag_start = (-1, -1)

    def pointerdown_accepted(self, event):

        if self.state == self.IDLE:
            logger.debug(f"Pointer down on valid source")
            self.drag_start = (event.clientX, event.clientY)
            self.state = self.READY
            event.stopPropagation()

    def pointermove(self, event) -> str:
        if self.state == self.READY:
            # Check if we've moved enough to consider this a drag
            dx = abs(event.clientX - self.drag_start[0])
            dy = abs(event.clientY - self.drag_start[1])

            if dx > self.DRAG_THRESHOLD_PX or dy > self.DRAG_THRESHOLD_PX:
                logger.debug("Drag threshold exceeded, entering DRAG_ACTIVE state")
                self.state = self.DRAGGING
        return self.state

    def transitioned_to_dragging(self, event) -> bool:
        if self.state != self.READY:
            return False
        self.pointermove(event)
        return self.state == self.DRAGGING

    def pointerup(self, event):
        if self.state == self.DRAGGING:
            # self.on_pointerup_accept(event)
            self.reset()


class DragManager:
    """
    Manages pointer state and interactions (click or drag) between source and target elements.

    This class tracks the state of pointer interactions and emits events at appropriate times.
    It supports both click-based and drag-based interaction patterns.
    """

    def __init__(self):
        """Initialize the PointerManager with default state and callbacks."""
        self._fsm = DragFsm()

        # Event callbacks
        self.on_pointerdown_accept = lambda event: False  # Default rejects all

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
