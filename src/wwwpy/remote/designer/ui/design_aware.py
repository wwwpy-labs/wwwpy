from __future__ import annotations

import logging
from dataclasses import dataclass

import js

from wwwpy.common.extension_point import ExtensionPointList

logger = logging.getLogger(__name__)


@dataclass
class IdentifyEvent:
    js_event: js.PointerEvent
    target: js.Element | None
    _action = None

    def set_action(self, action):
        self._action = action

    @property
    def is_action(self) -> bool:
        return self._action is not None

    def __str__(self):
        act = '' if self.is_action is None else f', action={self._action}'
        return f'IdentifyEvent(is_action={self.is_action}{act})'


class DesignAware:
    EP_LIST: ExtensionPointList[DesignAware] = ExtensionPointList()

    def find_action(self, ie: IdentifyEvent):
        raise NotImplemented()
