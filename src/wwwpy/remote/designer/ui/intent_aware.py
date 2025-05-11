from __future__ import annotations

import logging
from dataclasses import dataclass

import js

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.common.injectorlib import inject, injector
from wwwpy.remote.designer.ui.intent import Intent

logger = logging.getLogger(__name__)


@dataclass
class IdentifyIntentEvent:
    js_event: js.PointerEvent
    target: js.Element


def register_bindings():
    injector.bind(ExtensionPointList(), to=ExtensionPointList[IntentAware])


class IntentAware:
    EP_LIST: ExtensionPointList[IntentAware] = inject()

    def find(self, ie: IdentifyIntentEvent) -> Intent | None:
        raise NotImplemented()
