from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import js
from pyodide.ffi import create_proxy

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


class PointerManager:
    """
    Manages pointer state and interactions (click or drag) between source and target elements.

    This class tracks the state of pointer interactions and emits events at appropriate times.
    It supports both click-based and drag-based interaction patterns.
    """

    # States
    IDLE = "idle"
    CLICK_ACTIVE = "click_active"
    DRAG_ACTIVE = "drag_active"

    # Drag threshold (in pixels)
    DRAG_THRESHOLD = 5

    def __init__(self):
        """Initialize the PointerManager with default state and callbacks."""
        self.state = self.IDLE
        self.source_element = None
        self.current_target = None
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Install tracking
        self._install_count = 0

        # Event callbacks
        self.on_source_validation = lambda element: False  # Default rejects all
        self.on_target_validation = lambda element: False  # Default rejects all
        self.on_hover = lambda element, is_dragging: None  # Just emits events
        self.on_interaction_complete = lambda source, target: None
        self.on_interaction_cancel = lambda reason: None

        # Create JS event handlers with proper binding
        self._js_window__click = create_proxy(self._handle_click)
        self._js_window__pointerdown = create_proxy(self._handle_pointer_down)
        self._js_window__pointermove = create_proxy(self._handle_pointer_move)
        self._js_window__pointerup = create_proxy(self._handle_pointer_up)
        self._js_window__keydown = create_proxy(self._handle_keydown)

    def install(self):
        """Install event listeners to track pointer interactions."""
        self._install_count += 1
        if self._install_count > 1:
            logger.debug("PointerManager already installed, skipping")
            return

        logger.debug("Installing PointerManager event listeners")
        js.window.addEventListener('click', self._js_window__click)
        js.window.addEventListener('pointerdown', self._js_window__pointerdown)
        js.window.addEventListener('pointermove', self._js_window__pointermove)
        js.window.addEventListener('pointerup', self._js_window__pointerup)
        js.window.addEventListener('keydown', self._js_window__keydown)

    def uninstall(self):
        """Remove event listeners."""
        self._install_count -= 1
        if self._install_count > 0:
            logger.debug("PointerManager still in use, not uninstalling")
            return

        logger.debug("Uninstalling PointerManager event listeners")
        js.window.removeEventListener('click', self._js_window__click)
        js.window.removeEventListener('pointerdown', self._js_window__pointerdown)
        js.window.removeEventListener('pointermove', self._js_window__pointermove)
        js.window.removeEventListener('pointerup', self._js_window__pointerup)
        js.window.removeEventListener('keydown', self._js_window__keydown)

    def reset(self):
        """Reset to idle state without triggering any events."""
        logger.debug(f"Resetting PointerManager from state {self.state}")
        self.state = self.IDLE
        self.source_element = None
        self.current_target = None

    def _handle_click(self, event):
        """Handle click events for selection and interaction completion."""
        target_element = event.target

        # If we're in idle state, check if this is a valid source
        if self.state == self.IDLE:
            if self.on_source_validation(target_element):
                logger.debug(f"Valid source clicked: {target_element.id}")
                self.state = self.CLICK_ACTIVE
                self.source_element = target_element
                event.stopPropagation()
                return

        # If we're in click-active state
        elif self.state == self.CLICK_ACTIVE:
            # If clicking the same source again, deselect
            if target_element == self.source_element:
                logger.debug("Source clicked again, deselecting")
                self.on_interaction_cancel("source_reselected")
                self.reset()
                event.stopPropagation()
                return

            # If clicking a valid target, complete the interaction
            if self.on_target_validation(target_element):
                logger.debug(f"Valid target clicked: {target_element.id}")
                self.on_interaction_complete(self.source_element, target_element)
                self.reset()
                event.stopPropagation()
                return

    def _handle_pointer_down(self, event):
        """Handle pointer down events to initiate potential drag operations."""
        target_element = event.target

        # Only process in idle state and for valid sources
        if self.state == self.IDLE and self.on_source_validation(target_element):
            logger.debug(f"Pointer down on valid source: {target_element.id}")
            self.source_element = target_element
            self.drag_start_x = event.clientX
            self.drag_start_y = event.clientY
            # Don't set state yet - we'll wait for movement to determine if it's a click or drag

    def _handle_pointer_move(self, event):
        """Handle pointer move events for dragging and hovering."""
        # If we have a source element but haven't determined state yet
        if self.source_element and self.state == self.IDLE:
            # Check if we've moved enough to consider this a drag
            dx = abs(event.clientX - self.drag_start_x)
            dy = abs(event.clientY - self.drag_start_y)

            if dx > self.DRAG_THRESHOLD or dy > self.DRAG_THRESHOLD:
                logger.debug("Drag threshold exceeded, entering DRAG_ACTIVE state")
                self.state = self.DRAG_ACTIVE

        # Handle hover events in active states
        if self.state in [self.CLICK_ACTIVE, self.DRAG_ACTIVE]:
            target_element = self._get_element_at(event.clientX, event.clientY)
            is_dragging = (self.state == self.DRAG_ACTIVE)

            # If we've moved to a new element
            if target_element != self.current_target:
                self.current_target = target_element
                hover_event = HoverEvent(event, is_dragging=is_dragging, target_element=target_element)
                logger.debug(f"Hover event: {target_element.id if target_element else 'None'}, dragging={is_dragging}")
                self.on_hover(target_element, is_dragging)

    def _handle_pointer_up(self, event):
        """Handle pointer up events to complete drag operations."""
        if self.state == self.DRAG_ACTIVE:
            target_element = self._get_element_at(event.clientX, event.clientY)

            if target_element and self.on_target_validation(target_element):
                logger.debug(f"Drag completed on valid target: {target_element.id}")
                self.on_interaction_complete(self.source_element, target_element)
            else:
                logger.debug("Drag released on invalid target")
                self.on_interaction_cancel("invalid_target")

            self.reset()

    def _handle_keydown(self, event):
        """Handle keydown events for cancellation (Escape key)."""
        if self.state != self.IDLE and event.key == "Escape":
            logger.debug("Escape key pressed, cancelling interaction")
            self.on_interaction_cancel("escape_key")
            self.reset()

    def _get_element_at(self, x, y):
        """Get the element at the specified coordinates."""
        return js.document.elementFromPoint(x, y)
