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
class DeselectEvent(PMJsEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True


@dataclass
class HoverEvent(PMJsEvent):
    pass


@dataclass
class Action:
    label: str
    """Label to be displayed in the palette item."""

    selected: bool = False
    """True if the item is selected, False otherwise."""

    def on_selected(self): ...

    def on_hover(self, event: HoverEvent): ...

    def on_execute(self, event: DeselectEvent): ...

    def on_deselect(self): ...


@dataclass
class ActionChangedEvent(PMEvent):
    old: Action | None
    new: Action | None
