from __future__ import annotations
from dataclasses import dataclass

import js

import logging

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.remote.designer.ui.action import Action
from wwwpy.remote.jslib import get_deepest_element

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


class ActionIdentifier:

    def request_identification(self, js_event: js.PointerEvent) -> Action | None:
        target = get_deepest_element(js_event.clientX, js_event.clientY)
        ie = IdentifyEvent(js_event, target)
        for extension in DesignAware.EP_LIST.extensions:
            extension.find_action(ie)
            if ie.is_action:
                return ie._action

        return None
