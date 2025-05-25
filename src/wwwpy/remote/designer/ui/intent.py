from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

import js


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

    def on_selected(self): ...

    def on_hover(self, event: IntentEvent): ...

    def on_submit(self, event: IntentEvent) -> bool: ...

    """If return True, the intent is deselected, if False, it is not."""

    def on_deselected(self): ...


@dataclass
class IntentChangedEvent:
    old: Intent | None
    new: Intent | None
