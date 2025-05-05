import logging
from dataclasses import dataclass

import js

from wwwpy.common import injector
from wwwpy.remote import dict_to_py
from wwwpy.remote.designer import element_path
from wwwpy.remote.designer.helpers import _element_path_lbl
from wwwpy.remote.designer.ui.action_manager import Action, HoverEvent, DeselectEvent
from wwwpy.remote.designer.ui.element_selector import ElementSelector
from wwwpy.remote.designer.ui.property_editor import _rebase_element_path_to_origin_source
from wwwpy.remote.jslib import get_deepest_element

logger = logging.getLogger(__name__)


@dataclass
class SelectElementAction(Action):
    """Action to select an element in the designer."""
    label: str = 'Select'
    icon: str = 'select_element_icon'
    _next_element = None

    def on_hover(self, event: HoverEvent):
        self._set_selection_from_js_event(event.js_event)

    def on_execute(self, event: DeselectEvent):
        target = self._set_selection_from_js_event(event.js_event)
        if target is not None:
            self._set_toolbox_selection(target)
            event.accept()

    def _set_selection_from_js_event(self, event):
        # path = event.composedPath()
        # composed = path and len(path) > 0
        composed = 'disabled'
        # target = path[0] if composed else event.target
        target = _element_from_js_event(event)
        if target is None:
            logger.warning(f'set_selection: target is None {dict_to_py(event)}')
            return

        element_selector: ElementSelector = injector.get(ElementSelector)
        if not element_selector.element.isConnected:
            js.document.body.appendChild(element_selector.element)

        if not element_selector.is_selectable(target):
            logger.warning(f'set_selection: target is not selectable because o element_selector.is_selectable')
            return

        # unselectable = is_contained(target, self._palette.element)
        unselectable = False
        if unselectable or target == js.document.body or target == js.document.documentElement:
            target = None

        if element_selector.get_selected_element() == target:
            return target
        logger.debug(f'set_selection: {_pretty(target)}, unselectable: {unselectable}, composed: {composed}')
        js.console.log('set_selection console', event, event.composedPath())
        element_selector.set_selected_element(target)
        return target

    def _set_toolbox_selection(self, target):
        ep_live = element_path.element_path(target)
        logger.debug(f'Element path live: {ep_live}')
        ep_source = _rebase_element_path_to_origin_source(ep_live)
        logger.debug(f'Element path source: {ep_source}')
        message = 'ep_source is none' if ep_source is None else f'ep_source: {_element_path_lbl(ep_source)}'
        logger.warning(message)
        if ep_source is not None:
            from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
            tb = DevModeComponent.instance.toolbox
            tb._toolbox_state.selected_element_path = ep_live
            tb._restore_selected_element_path()
        else:
            logger.warning(message)


def _element_from_js_event(event):
    return get_deepest_element(event.clientX, event.clientY)


def _pretty(node: js.HTMLElement):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
