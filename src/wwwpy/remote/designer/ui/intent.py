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
    pass


@dataclass
class SubmitEvent(HoverEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True

@dataclass
class Intent:  # todo rename to Intent and keep action for AddElementAction
    label: str
    """Label to be displayed in the palette item."""

    selected: bool = False
    """True if the item is selected, False otherwise."""

    def on_selected(self): ...

    def on_hover(self, event: HoverEvent): ...

    # todo maybe rename to on_submit to convey that this could be accepted or not
    def on_execute(self, event: SubmitEvent): ...

    # todo rename to on_deselected
    def on_deselect(self): ...


@dataclass
class IntentChangedEvent(PMEvent):
    old: Intent | None
    new: Intent | None
