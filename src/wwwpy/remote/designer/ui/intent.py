from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

import js


@dataclass
class PMEvent: ...


@dataclass
class PMJsEvent(PMEvent):
    js_event: js.PointerEvent


TPE = TypeVar('TPE', bound=PMEvent)


@dataclass
class HoverEvent(PMJsEvent):
    deep_target: js.HTMLElement | None


@dataclass
class SubmitEvent(HoverEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True


@dataclass
class Intent:
    label: str
    """Label to be displayed in the palette item."""

    selected: bool = False
    """True if the item is selected, False otherwise."""

    def on_selected(self): ...

    def on_hover(self, event: HoverEvent): ...

    def on_submit(self, event: SubmitEvent): ...

    def on_deselected(self): ...


@dataclass
class IntentChangedEvent(PMEvent):
    old: Intent | None
    new: Intent | None
