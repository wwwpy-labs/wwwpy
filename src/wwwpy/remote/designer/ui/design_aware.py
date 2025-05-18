from __future__ import annotations

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent


class DesignAware:
    EP_REGISTRY: ExtensionPointRegistry[DesignAware] = ep_registry()

    def is_designer(self, hover_event: IntentEvent) -> bool | None:
        return False

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        return None

def is_designer(hover_event: IntentEvent) -> bool:
    for ep in DesignAware.EP_REGISTRY:
        if ep.is_designer(hover_event) is True:
            return True
    return False


def find_intent(intent_event: IntentEvent) -> Intent | None:
    if intent_event.deep_target is None:
        return None
    for extension in DesignAware.EP_REGISTRY:
        intent = extension.find_intent(intent_event)
        if intent:
            return intent
    return None
