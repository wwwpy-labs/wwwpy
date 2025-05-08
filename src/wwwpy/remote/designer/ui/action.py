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
class DeselectEvent(HoverEvent):
    accepted: bool = False

    def accept(self):
        self.accepted = True


# todo maybe split Action? extract ActionUi and ActionLogic, so the latter can stay in common
#  and this file can be cleaned up and partly moved to common
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
