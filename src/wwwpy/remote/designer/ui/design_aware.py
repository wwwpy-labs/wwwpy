from __future__ import annotations

import logging

import js

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent
from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)


class DesignAware:
    EP_REGISTRY: ExtensionPointRegistry[DesignAware] = ep_registry()

    # def is_selectable_js(self, js_event: js.PointerEvent) -> bool | None:
    #     return None

    def is_selectable_le(self, locator_event: LocatorEvent) -> bool | None:
        return None

    def locator_event_transformer(self, locator_event: LocatorEvent) -> LocatorEvent | None:
        return None

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        return None


def ep_is_selectable_le(locator_event: LocatorEvent) -> bool:
    except_none = [
        r for r in
        [(ep.__class__.__module__, ep.is_selectable_le(locator_event)) for ep in DesignAware.EP_REGISTRY]
        if r is not None
    ]
    bools = [r[1] for r in except_none]
    # if except_none and not any(except_none):  # list has at least one element and all are False
    #     return False
    if len(bools) == 0:
        return True
    if all(b is None for b in bools):
        logger.debug(f'all DesignAware.is_selectable_le returned None: {except_none}')
        return True

    if len(bools) > 0 and _all_false(bools):
        logger.debug(f'all DesignAware.is_selectable_le returned False or None: {except_none}')
        return False
    # logger.warning(f'all DesignAware.is_selectable returned True or None  : {except_none}')
    return True


def _all_false(lst: list[bool]) -> bool:
    """Check if all elements in the list are False."""
    return all(not item for item in lst)


def find_intent_da(js_event: js.PointerEvent) -> Intent | None:
    intent_event = IntentEvent(js_event)
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


def ep_locator_event_transformer(locator_event: LocatorEvent) -> LocatorEvent | None:
    for extension in DesignAware.EP_REGISTRY:
        try:
            new = extension.locator_event_transformer(locator_event)
            if new:
                return new
        except:
            logger.exception('find_intent EP error', stacklevel=2)
    return None
