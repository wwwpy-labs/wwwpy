from __future__ import annotations

import logging

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import Intent, IntentEvent

logger = logging.getLogger(__name__)


class IntentAware:
    EP_REGISTRY: ExtensionPointRegistry[IntentAware] = ep_registry()

    def find(self, hover_event: IntentEvent) -> Intent | None:
        raise NotImplemented()


def find_intent(hover_event: IntentEvent) -> Intent | None:
    for extension in IntentAware.EP_REGISTRY:
        intent = extension.find(hover_event)
        if intent:
            return intent
    return None
