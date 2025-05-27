from __future__ import annotations

import logging

import js

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.locator_js import locator_from
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent, Support
from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)


# class LocatorEvent2(Protocol):
#     locator_source: Locator
#     locator_live: Locator
#     locator_live_list: list[Locator]


class DesignAware:
    EP_REGISTRY: ExtensionPointRegistry[DesignAware] = ep_registry()

    # todo transform to to_locator_event
    def is_selectable(self, hover_event: IntentEvent) -> bool | None:
        return None

    def is_selectable_le(self, locator_event: LocatorEvent) -> bool | None:
        return None

    def location_attempt(self, hover_event: IntentEvent) -> LocatorEvent | Support | None:
        return None

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        return None


def is_selectable_da(hover_event: IntentEvent) -> bool:
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


def is_selectable_le(locator_event: LocatorEvent) -> bool:
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


def to_locator_event(hover_event: IntentEvent) -> LocatorEvent | None:
    if not is_selectable_da(hover_event):
        return None  # todo is_selectable should be incorporated into to_locator_event
    res = [
        le for le in
        [ep.location_attempt(hover_event) for ep in DesignAware.EP_REGISTRY]
        if le is not None
    ]
    return _default_to_locator_event(hover_event)


def _default_to_locator_event(hover_event: IntentEvent) -> LocatorEvent | None:
    event = hover_event.js_event
    target = hover_event.deep_target
    if not target:
        return None
    if target == js.document.body or target == js.document.documentElement:
        return None

    locator = locator_from(target)
    if not locator:
        logger.warning(f'locator_from returned None for target: {target}')
        return None

    rect = target.getBoundingClientRect()
    xy = event.clientX - rect.left, event.clientY - rect.top
    return LocatorEvent(
        locator=locator,
        main_element=target,
        main_xy=xy
    )
