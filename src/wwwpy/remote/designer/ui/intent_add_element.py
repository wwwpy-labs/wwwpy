import dataclasses
import logging
from dataclasses import dataclass, field

import js

from wwwpy.common import modlib
from wwwpy.common.asynclib import create_task_safe
from wwwpy.common.designer.canvas_selection import CanvasSelection
from wwwpy.common.designer.code_edit import add_element, AddResult, AddFailed
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.html_locator import path_to_index
from wwwpy.common.designer.locator_lib import Locator
from wwwpy.common.designer.ui._drop_indicator_svg import position_for
from wwwpy.common.injectorlib import injector
from wwwpy.remote.designer.helpers import _element_path_lbl
from wwwpy.remote.designer.locator_js import locator_from
from wwwpy.remote.designer.ui.design_aware import to_locator_event
from wwwpy.remote.designer.ui.floater_drop_indicator import DropIndicatorFloater
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent
from wwwpy.remote.designer.ui.locator_event import LocatorEvent
from wwwpy.remote.designer.ui.property_editor import _rebase_element_path_to_origin_source

# from wwwpy.remote.designer.ui.toolbox import _open_error_reporter_window

logger = logging.getLogger(__name__)

_tool = DropIndicatorFloater()
_tool.transition = True


@dataclass
class AddElementIntent(Intent):
    element_def: ElementDefBase = None
    add_element: callable = field(default_factory=lambda: _add_component)

    def __post_init__(self):
        self._tool = _tool

    def on_selected(self):
        self._tool.show()

    def on_deselected(self):
        self._tool.hide()

    def on_hover(self, locator_event: LocatorEvent):
        assert isinstance(locator_event, LocatorEvent), f'Expected LocatorEvent, got {type(locator_event)}'
        tool = self._tool
        if not tool.element.isConnected:
            js.document.body.appendChild(tool.element)
        tool.set_reference_geometry2(
            locator_event.main_element.getBoundingClientRect(),
            locator_event.position()
        )
        tool.show()

    def on_hover_old(self, event: IntentEvent):
        self._set_selection_from_js_event(event)

    def on_submit(self, locator_event: LocatorEvent) -> bool:
        locator_live = locator_event.locator
        locator_source = _rebase_element_path_to_origin_source(locator_live)
        ep_log = \
            f'Locator live: {locator_live} origin: {locator_live.origin}' + '\n' + \
            f'Locator source: {locator_source}'
        message = 'locator_source is none' if locator_source is None else f'locator_source: {_element_path_lbl(locator_source)}'
        if locator_source is not None:
            logger.debug(ep_log + '\n' + message)
            position = locator_event.position()
            self.add_element(locator_source, position, self.element_def)
            self._tool.hide()
            return True
        else:
            logger.warning(message)
            return False

    def _get_position(self, locator_event):
        rect = locator_event.main_element.getBoundingClientRect()
        rx, ry = locator_event.main_xy
        position = position_for(rect.width, rect.height, rx, ry, )
        return position

    # def on_submit_old(self, event: IntentEvent) -> bool:
    #     target, position = self._set_selection_from_js_event(event)
    #     if target is not None:
    #         if is_instance_of(target, js.HTMLElement):
    #             target: js.HTMLElement
    #             self.add_element(target, position)
    #             return True
    #         else:
    #             logger.warning(f'set_selection: target is not a HTMLElement {dict_to_py(target)}')
    #             js.alert('Target is not an HTMLElement')
    #     return False

    def _set_selection_from_js_event(self, intent_event: IntentEvent):
        tool = self._tool
        if not tool.element.isConnected:
            js.document.body.appendChild(tool.element)
        le = to_locator_event(intent_event)
        if le is not None:
            rect = le.main_element.getBoundingClientRect()
            rx, ry = le.main_xy
            position = position_for(rect.width, rect.height, rx, ry, )
            tool.show()
            tool.set_reference_geometry2(rect, position)
        else:
            tool.hide()
        # old
        # event = intent_event.js_event
        # target = intent_event.deep_target
        #
        # tool = self._tool
        # if not tool.element.isConnected:
        #     js.document.body.appendChild(tool.element)
        #
        # unselectable = not is_selectable(intent_event)
        # if unselectable or target == js.document.body or target == js.document.documentElement:
        #     target = None
        #
        # logger.debug(f'set_selection: {_pretty(target)}, unselectable: {unselectable}')
        # position = None
        # if target:
        #     rect = target.getBoundingClientRect()
        #     rx, ry = event.clientX - rect.left, event.clientY - rect.top
        #     position = position_for(rect.width, rect.height, rx, ry, )
        #     self._tool.show()
        #     self._tool.set_reference_geometry2(rect, position)
        # else:
        #     self._tool.hide()
        # return target, position

    def _add_element(self, target: js.HTMLElement, position: Position):
        ep_live = locator_from(target)
        ep_source = _rebase_element_path_to_origin_source(ep_live)
        ep_log = \
            f'Locator live: {ep_live} position: {position}' + '\n' + \
            f'Locator source: {ep_source}'
        message = 'ep_source is none' if ep_source is None else f'ep_source: {_element_path_lbl(ep_source)}'
        if ep_source is not None:
            logger.debug(ep_log + '\n' + message)
            _add_component(ep_source, position, self.element_def)
        else:
            logger.warning(message)


def _pretty(node: js.HTMLElement):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)


def _add_component(el_path: Locator, position: Position,
                   element_def: ElementDefBase):
    file = modlib._find_module_path(el_path.class_module)
    old_source = file.read_text()

    path_index = path_to_index(el_path.path)
    add_result = add_element(old_source, el_path.class_name, element_def, path_index, position)

    if isinstance(add_result, AddResult):
        logger.debug(f'write_module_file len={len(add_result.source_code)} el_path={el_path}')
        injector.get(CanvasSelection).current_selection = dataclasses.replace(el_path, path=add_result.node_path)

        async def write_source_file():
            from wwwpy.server.designer import rpc
            write_res = await rpc.write_module_file(el_path.class_module, add_result.source_code)
            logger.debug(f'write_module_file res={write_res}')

        create_task_safe((write_source_file()))
    elif isinstance(add_result, AddFailed):
        js.alert('Sorry, an error occurred while adding the component.')
        # _open_error_reporter_window(
        #     'Error report data:\n\n' + add_result.exception_report_b64,
        #     title='Error report add_component - wwwpy'
        # )
