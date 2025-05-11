from __future__ import annotations

import logging
from dataclasses import dataclass

import js

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.remote.designer.ui.intent import Intent

logger = logging.getLogger(__name__)


@dataclass
class IdentifyActionEvent:
    js_event: js.PointerEvent
    target: js.Element


class IntentAware:
    EP_LIST: ExtensionPointList[IntentAware] = ExtensionPointList()  # todo use inject(static=True)

    def find_action(self, ie: IdentifyActionEvent) -> Intent | None:
        raise NotImplemented()
