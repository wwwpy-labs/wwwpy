from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

import js


@dataclass
class PMEvent: ...


TPE = TypeVar('TPE', bound=PMEvent)


@dataclass
class IntentEvent(PMEvent):
    js_event: js.PointerEvent
    deep_target: js.HTMLElement | None


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
class IntentChangedEvent(PMEvent):
    old: Intent | None
    new: Intent | None
