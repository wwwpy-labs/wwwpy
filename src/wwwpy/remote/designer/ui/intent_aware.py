from __future__ import annotations

import logging

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import Intent, HoverEvent

logger = logging.getLogger(__name__)


class IntentAware:
    EP_LIST: ExtensionPointRegistry[IntentAware] = ep_registry()

    def find(self, hover_event: HoverEvent) -> Intent | None:
        raise NotImplemented()


def find_intent(hover_event: HoverEvent) -> Intent | None:
    for extension in IntentAware.EP_LIST:
        intent = extension.find(hover_event)
        if intent:
            return intent
    return None
