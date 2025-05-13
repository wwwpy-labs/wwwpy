from __future__ import annotations

import logging

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.common.injectorlib import inject, injector
from wwwpy.remote.designer.ui.intent import Intent, HoverEvent

logger = logging.getLogger(__name__)


def register_bindings():
    injector.bind(ExtensionPointList(), to=ExtensionPointList[IntentAware])


class IntentAware:
    EP_LIST: ExtensionPointList[IntentAware] = inject()

    def find(self, hover_event: HoverEvent) -> Intent | None:
        raise NotImplemented()


def find_intent(hover_event: HoverEvent) -> Intent | None:
    for extension in IntentAware.EP_LIST.extensions:
        intent = extension.find(hover_event)
        if intent:
            return intent
    return None
