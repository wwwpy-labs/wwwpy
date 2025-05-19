from __future__ import annotations

import logging

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent

logger = logging.getLogger(__name__)


class DesignAware:
    EP_REGISTRY: ExtensionPointRegistry[DesignAware] = ep_registry()

    # todo refactor name to is_selectable (negate logic)
    def is_designer(self, hover_event: IntentEvent) -> bool | None:
        return False

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        return None

    # todo implement find_element_path
    # def find_element_path(self, hover_event: IntentEvent) -> ElementPath | None:
    #     """In order, this should be """
    #     return None


def is_designer(hover_event: IntentEvent) -> bool:
    for ep in DesignAware.EP_REGISTRY:
        if ep.is_designer(hover_event) is True:
            return True
    return False


def find_intent(intent_event: IntentEvent) -> Intent | None:
    if intent_event.deep_target is None:
        return None
    for extension in DesignAware.EP_REGISTRY:
        try:
            intent = extension.find_intent(intent_event)
            if intent:
                return intent
        except:
            logger.exception('find_intent EP error', stacklevel=2)
    return None

# def find_element_path(hover_event: IntentEvent) -> ElementPath | None:
#     if hover_event.deep_target is None:
#         return None
#     for extension in DesignAware.EP_REGISTRY:
#         path = extension.find_element_path(hover_event)
#         if path:
#             return path
#     return None
