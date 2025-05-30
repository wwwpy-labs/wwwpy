from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from functools import cached_property

import js

from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)


# todo we could remove IntentEvent and use directly js.PointerEvent
#  or we could use LocatorEvent. IntentManager could materialize LocatorEvent somehow (using injector)
@dataclass
class IntentEvent:
    js_event: js.PointerEvent

    @cached_property
    def deep_target(self) -> js.HTMLElement | None:
        from wwwpy.remote.jslib import get_deepest_element
        return get_deepest_element(self.js_event.clientX, self.js_event.clientY)


def js_event_to_locator_event_default(js_event: js.PointerEvent) -> LocatorEvent | None:
    """Convert a JavaScript PointerEvent to a LocatorEvent."""
    from wwwpy.remote.designer.ui.design_aware import ep_is_selectable_le
    locator_event = LocatorEvent.from_pointer_event(js_event)

    from wwwpy.remote.designer.ui.design_aware import ep_locator_event_transformer
    le_transformed = ep_locator_event_transformer(locator_event)

    if le_transformed is not None:
        return le_transformed

    if not ep_is_selectable_le(locator_event):
        return None

    return locator_event


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
        """If return True, the intent is deselected, if False, it is not."""

    def on_deselected(self):
        ...

    def on_hover_js(self, js_event: js.PointerEvent):
        """Handle hover event from JavaScript."""
        event = js_event_to_locator_event_default(js_event)
        if event:
            self.on_hover(event)

    def on_submit_js(self, js_event: js.PointerEvent) -> bool:
        """Handle submit event from JavaScript."""
        event = js_event_to_locator_event_default(js_event)
        if event:
            return self.on_submit(event)
        return False


@dataclass
class IntentChangedEvent:
    old: Intent | None
    new: Intent | None


class Support(str, Enum):
    CONTAINER = 'CONTAINER'
