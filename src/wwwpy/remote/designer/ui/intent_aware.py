from __future__ import annotations

import logging
from dataclasses import dataclass

import js

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.remote.designer.ui.intent import Intent

logger = logging.getLogger(__name__)


@dataclass
class IdentifyIntentEvent:
    js_event: js.PointerEvent
    target: js.Element


class IntentAware:
    EP_LIST: ExtensionPointList[IntentAware] = ExtensionPointList()  # todo use inject(static=True)

    def find(self, ie: IdentifyIntentEvent) -> Intent | None:
        raise NotImplemented()
