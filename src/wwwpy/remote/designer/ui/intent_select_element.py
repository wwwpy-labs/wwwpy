import logging
from dataclasses import dataclass
from functools import cached_property

import js

from wwwpy.common.designer.canvas_selection import CanvasSelection
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_py
from wwwpy.remote.designer.helpers import _element_path_lbl
from wwwpy.remote.designer.locator_js import locator_from
from wwwpy.remote.designer.ui.design_aware import is_selectable
from wwwpy.remote.designer.ui.element_selector import ElementSelector
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent
from wwwpy.remote.designer.ui.property_editor import _rebase_element_path_to_origin_source

logger = logging.getLogger(__name__)


@dataclass
class SelectElementIntent(Intent):
    """Action to select an element in the designer."""
    label: str = 'Select'
    icon: str = 'select_element_icon'

    def on_hover(self, event: IntentEvent):
        logger.debug(f'on_hover {event}')
        self._set_selection_from_js_event(event)

    def on_submit(self, event: IntentEvent) -> bool:
        logger.debug(f'on_submit {event}')
        target = self._set_selection_from_js_event(event)
        has_target = target is not None
        if has_target:
            self._set_toolbox_selection(target)
        return has_target

    def _set_selection_from_js_event(self, intent_event: IntentEvent):
        event = intent_event.js_event
        target = intent_event.deep_target
        if target is None:
            logger.warning(f'set_selection: target is None {dict_to_py(event)}')
            return

        # element_selector: ElementSelector = injector.get(ElementSelector)
        element_selector: ElementSelector = self._element_selector
        if not element_selector.element.isConnected:
            js.document.body.appendChild(element_selector.element)

        if not element_selector.is_selectable(target):
            logger.warning(f'set_selection: target is not selectable because o element_selector.is_selectable')
            return

        # unselectable = is_contained(target, self._palette.element)
        unselectable = not is_selectable(intent_event)
        if unselectable:
            logger.debug(f'set_selection: target is unselectable')

        if unselectable or target == js.document.body or target == js.document.documentElement:
            target = None

        if element_selector.get_selected_element() == target:
            return target
        logger.debug(f'set_selection: {_pretty(target)}, unselectable: {unselectable}')
        element_selector.set_selected_element(target)
        return target

    def _set_toolbox_selection(self, target):
        ep_live = locator_from(target)
        logger.debug(f'Element path live: {ep_live}')
        ep_source = _rebase_element_path_to_origin_source(ep_live)
        logger.debug(f'Element path source: {ep_source}')
        message = 'ep_source is none' if ep_source is None else f'ep_source: {_element_path_lbl(ep_source)}'
        logger.warning(message)
        if ep_source is not None:
            injector.get(CanvasSelection).current_selection = ep_source
        else:
            logger.warning(message)

    @cached_property
    def _element_selector(self) -> ElementSelector:
        return ElementSelector()


def _pretty(node: js.HTMLElement):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
