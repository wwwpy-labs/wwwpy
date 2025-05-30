import logging
from dataclasses import dataclass
from functools import cached_property

import js

from wwwpy.common.designer.canvas_selection import CanvasSelection
from wwwpy.common.injectorlib import injector
from wwwpy.remote.designer.ui.element_selector import ElementSelector
from wwwpy.remote.designer.ui.intent import Intent
from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)


@dataclass
class SelectElementIntent(Intent):
    """Action to select an element in the designer."""
    label: str = 'Select'
    icon: str = 'select_element_icon'

    def on_hover(self, event: LocatorEvent):
        logger.debug(f'on_hover {event}')
        self._set_selection_from_js_event(event)

    def on_submit(self, event: LocatorEvent) -> bool:
        logger.debug(f'on_submit {event}')
        self._set_selection_from_js_event(event)
        injector.get(CanvasSelection).current_selection = event.locator
        return True

    def _set_selection_from_js_event(self, le: LocatorEvent):
        element_selector: ElementSelector = self._element_selector
        if not element_selector.element.isConnected:
            js.document.body.appendChild(element_selector.element)

        target = None
        if le is not None:
            target = le.main_element

        if element_selector.get_selected_element() != target:
            element_selector.set_selected_element(target)

        return target

    @cached_property
    def _element_selector(self) -> ElementSelector:
        return ElementSelector()


def _pretty(node: js.HTMLElement):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
