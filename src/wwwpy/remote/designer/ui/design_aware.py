from __future__ import annotations

import logging
from dataclasses import dataclass

import js

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.remote.designer.ui.action import Action

logger = logging.getLogger(__name__)


@dataclass
class IdentifyEvent:
    js_event: js.PointerEvent
    target: js.Element | None


class DesignAware:
    EP_LIST: ExtensionPointList[DesignAware] = ExtensionPointList()

    def find_action(self, ie: IdentifyEvent) -> Action | None:
        raise NotImplemented()
