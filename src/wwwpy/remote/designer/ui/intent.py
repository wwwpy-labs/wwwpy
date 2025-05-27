from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

import js

from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    """The phase of the intent."""
    SELECT = 'SELECT'
    """Intent is selected."""
    HOVER = 'HOVER'
    """Inform the intent of some hover event."""
    SUBMIT = 'SUBMIT'
    """Intent is submitted."""
    DESELECT = 'DESELECT'
    """Intent is deselected."""


# todo we could remove IntentEvent and use directly js.PointerEvent
#  or we could use LocatorEvent. IntentManager could materialize LocatorEvent somehow (using injector)
@dataclass
class IntentEvent:
    js_event: js.PointerEvent

    @cached_property
    def deep_target(self) -> js.HTMLElement | None:
        from wwwpy.remote.jslib import get_deepest_element
        return get_deepest_element(self.js_event.clientX, self.js_event.clientY)


@dataclass
class Intent:
    label: str
    """Label to be displayed in the palette item."""

    selected: bool = False
    """True if the item is selected, False otherwise."""

    def on_selected(self):
        ...

    def on_hover(self, _: LocatorEvent):
        ...

    def on_submit(self, _: LocatorEvent) -> bool:
        ...

    """If return True, the intent is deselected, if False, it is not."""

    def on_deselected(self):
        ...

    def on_hover_js(self, js_event: js.PointerEvent):
        """Handle hover event from JavaScript."""
        event = js_event_to_locator_event(js_event)
        if event:
            self.on_hover(event)

    def on_submit_js(self, js_event: js.PointerEvent) -> bool:
        """Handle submit event from JavaScript."""
        event = js_event_to_locator_event(js_event)
        if event:
            return self.on_submit(event)
        return False


def js_event_to_locator_event(js_event: js.PointerEvent) -> LocatorEvent | None:
    """Convert a JavaScript PointerEvent to a LocatorEvent."""
    from wwwpy.remote.designer.ui.design_aware import is_selectable_le
    event = LocatorEvent.from_pointer_event(js_event)
    if not is_selectable_le(event):
        return None
    return event


@dataclass
class IntentChangedEvent:
    old: Intent | None
    new: Intent | None


class IntentExecutor:
    def __init__(self, intent: Intent):
        self._intent = intent

    def on_hover(self, js_event: js.PointerEvent): ...

    def on_submit(self, js_event: js.PointerEvent) -> bool: ...


class DefaultIntentExecutor(IntentExecutor):

    def __init__(self, intent: Intent):
        super().__init__(intent)

    def on_hover(self, js_event: js.PointerEvent):
        event = LocatorEvent.from_pointer_event(js_event)
        if event:
            self._intent.on_hover(event)

    def on_submit(self, js_event: js.PointerEvent) -> bool:
        event = LocatorEvent.from_pointer_event(js_event)
        if event:
            return self._intent.on_submit(event)


class Support(str, Enum):
    CONTAINER = 'CONTAINER'
