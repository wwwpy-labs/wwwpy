from __future__ import annotations

import logging
from dataclasses import dataclass

import js

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.remote.designer.ui.action import Action

logger = logging.getLogger(__name__)


@dataclass
class IdentifyActionEvent:
    js_event: js.PointerEvent
    target: js.Element


class ActionAware:
    EP_LIST: ExtensionPointList[ActionAware] = ExtensionPointList()

    def find_action(self, ie: IdentifyActionEvent) -> Action | None:
        raise NotImplemented()
