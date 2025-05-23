from __future__ import annotations

import logging
from dataclasses import dataclass

from wwwpy.common.designer.locator_lib import Locator
from wwwpy.common.type_listener import TypeListeners

logger = logging.getLogger(__name__)


@dataclass
class CanvasSelectionChangeEvent:
    old: Locator | None
    new: Locator | None


class CanvasSelection:
    """At the time of writing, this class is listened by the old infrastructure, but
    it is not updated by it. Who writes it is the new infrastructure.
    """
    current_selection: Locator | None
    """It looks like the ElementPath should have Origin.live"""

    def __init__(self):
        self._current_selection = None
        self.on_change: TypeListeners[CanvasSelectionChangeEvent] = TypeListeners(CanvasSelectionChangeEvent)

    @property
    def current_selection(self) -> Locator | None:
        return self._current_selection

    @current_selection.setter
    def current_selection(self, value: Locator | None):
        old = self._current_selection
        self._current_selection = value
        event = CanvasSelectionChangeEvent(old, value)
        logger.debug(f'CanvasSelection: {old} -> {value}')
        self.on_change.notify(event)
