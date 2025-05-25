from __future__ import annotations

import logging

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent

logger = logging.getLogger(__name__)


class DesignAware:
    EP_REGISTRY: ExtensionPointRegistry[DesignAware] = ep_registry()

    def is_selectable(self, hover_event: IntentEvent) -> bool | None:
        return None

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        return None

    # todo implement find_element_path
    # def find_element_path(self, hover_event: IntentEvent) -> ElementPath | None:
    #     """In order, this should be """
    #     return None


def is_selectable(hover_event: IntentEvent) -> bool:
    except_none = [
        r for r in
        [(ep.__class__.__module__, ep.is_selectable(hover_event)) for ep in DesignAware.EP_REGISTRY]
        if r is not None
    ]
    bools = [r[1] for r in except_none]
    # if except_none and not any(except_none):  # list has at least one element and all are False
    #     return False
    if len(bools) == 0:
        return True
    if all(b is None for b in bools):
        logger.debug(f'all DesignAware.is_selectable returned None: {except_none}')
        return True

    if len(bools) > 0 and _all_false(bools):
        logger.debug(f'all DesignAware.is_selectable returned False or None: {except_none}')
        return False
    # logger.warning(f'all DesignAware.is_selectable returned True or None  : {except_none}')
    return True


def _all_false(lst: list[bool]) -> bool:
    """Check if all elements in the list are False."""
    return all(not item for item in lst)

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
