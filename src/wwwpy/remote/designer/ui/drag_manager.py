from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import js
from pyodide.ffi import create_proxy

from wwwpy.remote import eventlib

logger = logging.getLogger(__name__)


@dataclass
class PointerEvent:
    """Base class for pointer-related events."""
    event: js.Event
    is_spent: bool = False

    def spend(self):
        """Mark the event as spent (handled)."""
        self.is_spent = True


@dataclass
class HoverEvent(PointerEvent):
    """Event emitted when pointer moves over potential targets."""
    is_dragging: bool = False
    target_element: Optional[js.HTMLElement] = None


@dataclass
class InteractionEvent(PointerEvent):
    """Event emitted when an interaction completes or cancels."""
    source_element: Optional[js.HTMLElement] = None
    target_element: Optional[js.HTMLElement] = None


class Cancelled:
    source_reselected = "source_reselected"
    invalid_target = "invalid_target"
    escape_key = "escape_key"


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
        self.source_element = None
        self.current_target = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Event callbacks
        self.on_pointerdown_accept = lambda event, element: False  # Default rejects all
        self.on_target_validation = lambda element: False  # Default rejects all
        self.on_hover = lambda event, element, is_dragging: None  # Just emits events
        self.on_interaction_complete = lambda source, target: None
        self.on_interaction_cancel = lambda reason: None

    def install(self):
        eventlib.add_event_listeners(self)

    def uninstall(self):
        eventlib.remove_event_listeners(self)

    def reset(self):
        """Reset to idle state without triggering any events."""
        logger.debug(f"Resetting PointerManager from state {self.state}")
        self.state = self.IDLE
        self.source_element = None
        self.current_target = None

    def _js_window__pointerdown(self, event):
        """Handle pointer down events to initiate potential drag operations."""
        target_element = event.target

        # Only process in idle state and for valid sources
        if self.state == self.IDLE and self.on_pointerdown_accept(event, target_element):
            logger.debug(f"Pointer down on valid source: {target_element.id}")
            self.source_element = target_element
            self.drag_start_x = event.clientX
            self.drag_start_y = event.clientY

            # In tests we need to transition to CLICK_ACTIVE immediately
            # to make the state machine work correctly with simulated events
            self.state = self.READY

            # Mark the event as handled
            event.stopPropagation()

    def _js_window__pointermove(self, event):
        """Handle pointer move events for dragging and hovering."""
        # If we have a source element and are in CLICK_ACTIVE state
        if self.source_element and self.state == self.READY:
            # Check if we've moved enough to consider this a drag
            dx = abs(event.clientX - self.drag_start_x)
            dy = abs(event.clientY - self.drag_start_y)

            if dx > self.DRAG_THRESHOLD_PX or dy > self.DRAG_THRESHOLD_PX:
                logger.debug("Drag threshold exceeded, entering DRAG_ACTIVE state")
                self.state = self.DRAGGING


    def _js_window__pointerup(self, event):
        """Handle pointer up events to complete drag operations."""
        if self.state == self.DRAGGING:
            target_element = self._get_element_at(event.clientX, event.clientY)

            if target_element and self.on_target_validation(target_element):
                logger.debug(f"Drag completed on valid target: {target_element.id}")
                self.on_interaction_complete(self.source_element, target_element)
            else:
                logger.debug("Drag released on invalid target")
                self.on_interaction_cancel(Cancelled.invalid_target)

            self.reset()

    def _js_window__keydown(self, event):
        """Handle keydown events for cancellation (Escape key)."""
        logger.debug(f"Keydown event: {event.key}")
        if self.state != self.IDLE and event.key == "Escape":
            logger.debug("Escape key pressed, cancelling interaction")
            self.on_interaction_cancel(Cancelled.escape_key)
            self.reset()
            event.preventDefault()
            event.stopPropagation()

    def _get_element_at(self, x, y):
        """Get the element at the specified coordinates."""
        return js.document.elementFromPoint(x, y)
