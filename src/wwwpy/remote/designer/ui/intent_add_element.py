import logging
from dataclasses import dataclass

import js

from wwwpy.common.designer.canvas_selection import CanvasSelection
from wwwpy.common.injectorlib import injector
from wwwpy.remote.designer import element_path
from wwwpy.remote.designer.helpers import _element_path_lbl
from wwwpy.remote.designer.ui.floater_drop_indicator import DropIndicatorFloater
from wwwpy.remote.designer.ui.intent import SubmitEvent, HoverEvent, Intent
from wwwpy.remote.designer.ui.property_editor import _rebase_element_path_to_origin_source
from wwwpy.remote.jslib import get_deepest_element

logger = logging.getLogger(__name__)


@dataclass
class AddElementIntent(Intent):
    """Action to select an element in the designer."""
    label: str = 'Add element'

    def __post_init__(self):
        # self._tool = WeirdSelectionIndicatorTool()
        self._tool = DropIndicatorFloater()
        self._tool.transition = True
        self._selected = None

    def on_hover(self, event: HoverEvent):
        self._set_selection_from_js_event(event)

    def on_submit(self, event: SubmitEvent):
        # todo add a self.callback_something to notify (ElementPath, Position)
        target = self._set_selection_from_js_event(event)
        # self._tool.element.remove()
        if target is not None:
            self._set_toolbox_selection(target)
            event.accept()

    def _set_selection_from_js_event(self, hover_event: HoverEvent):
        event = hover_event.js_event

        target = get_deepest_element(event.clientX, event.clientY)

        tool = self._tool
        if not tool.element.isConnected:
            js.document.body.appendChild(tool.element)

        # if not element_selector.is_selectable(target):
        #     logger.warning(f'set_selection: target is not selectable because o element_selector.is_selectable')
        #     return

        # unselectable = is_contained(target, self._palette.element)
        unselectable = False
        if unselectable or target == js.document.body or target == js.document.documentElement:
            target = None

        # if self._selected == target:
        #     return target
        logger.debug(f'set_selection: {_pretty(target)}, unselectable: {unselectable}')
        js.console.log('set_selection console', event, event.composedPath())
        if target:
            self._tool.set_reference_geometry2(target.getBoundingClientRect(), event)
        self._selected = target
        return target

    def _set_toolbox_selection(self, target):
        ep_live = element_path.element_path(target)
        logger.debug(f'Element path live: {ep_live}')
        ep_source = _rebase_element_path_to_origin_source(ep_live)
        logger.debug(f'Element path source: {ep_source}')
        message = 'ep_source is none' if ep_source is None else f'ep_source: {_element_path_lbl(ep_source)}'
        logger.warning(message)
        if ep_source is not None:
            injector.get(CanvasSelection).current_selection = ep_source
        else:
            logger.warning(message)


def _pretty(node: js.HTMLElement):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
