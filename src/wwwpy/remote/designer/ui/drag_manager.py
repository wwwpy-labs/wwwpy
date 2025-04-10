from __future__ import annotations

import logging

from pyodide.ffi import create_proxy

from wwwpy.remote import eventlib

logger = logging.getLogger(__name__)


class DragManager:
    """
    Manages pointer state and interactions (click or drag) between source and target elements.

    This class tracks the state of pointer interactions and emits events at appropriate times.
    It supports both click-based and drag-based interaction patterns.
    """

    # States
    IDLE = "idle"
    READY = "ready"
    DRAGGING = "dragging"

    DRAG_THRESHOLD_PX = 5

    def __init__(self):
        """Initialize the PointerManager with default state and callbacks."""
        self.state = self.IDLE
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Event callbacks
        self.on_pointerdown_accept = lambda event: False  # Default rejects all
        self.on_pointerup_accept = lambda event: False  # Default rejects all

    def install(self):
        eventlib.add_event_listeners(self)

    def uninstall(self):
        eventlib.remove_event_listeners(self)

    def reset(self):
        """Reset to idle state without triggering any events."""
        logger.debug(f"Resetting PointerManager from state {self.state}")
        self.state = self.IDLE

    def _js_window__pointerdown(self, event):
        """Handle pointer down events to initiate potential drag operations."""

        # Only process in idle state and for valid sources
        if self.state == self.IDLE and self.on_pointerdown_accept(event):
            logger.debug(f"Pointer down on valid source")
            self.drag_start_x = event.clientX
            self.drag_start_y = event.clientY
            self.state = self.READY
            event.stopPropagation()

    def _js_window__pointermove(self, event):
        """Handle pointer move events for dragging and hovering."""
        if self.state == self.READY:
            # Check if we've moved enough to consider this a drag
            dx = abs(event.clientX - self.drag_start_x)
            dy = abs(event.clientY - self.drag_start_y)

            if dx > self.DRAG_THRESHOLD_PX or dy > self.DRAG_THRESHOLD_PX:
                logger.debug("Drag threshold exceeded, entering DRAG_ACTIVE state")
                self.state = self.DRAGGING

    def _js_window__pointerup(self, event):
        """Handle pointer up events to complete drag operations."""
        if self.state == self.DRAGGING:
            self.on_pointerup_accept(event)
            self.reset()
