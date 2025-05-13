import logging
from dataclasses import dataclass

import js

from wwwpy.common import modlib
from wwwpy.common.asynclib import create_task_safe
from wwwpy.common.designer.canvas_selection import CanvasSelection
from wwwpy.common.designer.code_edit import add_component, AddResult, AddFailed
from wwwpy.common.designer.element_library import ElementDef
from wwwpy.common.designer.element_path import ElementPath
from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.html_locator import path_to_index
from wwwpy.common.designer.ui._drop_indicator_svg import position_for
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_py
from wwwpy.remote.designer import element_path
from wwwpy.remote.designer.helpers import _element_path_lbl
from wwwpy.remote.designer.ui.floater_drop_indicator import DropIndicatorFloater
from wwwpy.remote.designer.ui.intent import SubmitEvent, HoverEvent, Intent
from wwwpy.remote.designer.ui.property_editor import _rebase_element_path_to_origin_source
from wwwpy.remote.designer.ui.toolbox import _open_error_reporter_window
from wwwpy.remote.jslib import get_deepest_element, is_instance_of

logger = logging.getLogger(__name__)


@dataclass
class AddElementIntent(Intent):
    element_def: ElementDef = None

    @property
    def label(self) -> str:
        return f'Add {self.element_def.tag_name}'

    def __post_init__(self):
        self._tool = DropIndicatorFloater()
        self._tool.transition = True

    def on_hover(self, event: HoverEvent):
        self._set_selection_from_js_event(event)

    def on_submit(self, event: SubmitEvent):
        target, position = self._set_selection_from_js_event(event)
        if target is not None:
            if is_instance_of(target, js.HTMLElement):
                target: js.HTMLElement
                self._add_element(target, position)
                event.accept()
            else:
                logger.warning(f'set_selection: target is not a HTMLElement {dict_to_py(target)}')
                js.alert('Target is not an HTMLElement')

    def _set_selection_from_js_event(self, hover_event: HoverEvent):
        event = hover_event.js_event

        target = get_deepest_element(event.clientX, event.clientY)

        tool = self._tool
        if not tool.element.isConnected:
            js.document.body.appendChild(tool.element)

        unselectable = False
        if unselectable or target == js.document.body or target == js.document.documentElement:
            target = None

        # if self._selected == target:
        #     return target
        logger.debug(f'set_selection: {_pretty(target)}, unselectable: {unselectable}')
        js.console.log('set_selection console', event, event.composedPath())
        position = None
        if target:
            rect = target.getBoundingClientRect()
            rx, ry = event.clientX - rect.left, event.clientY - rect.top
            position = position_for(rect.width, rect.height, rx, ry, )
            self._tool.set_reference_geometry2(rect, position)
        return target, position

    def _add_element(self, target: js.HTMLElement, position: Position):
        ep_live = element_path.element_path(target)
        logger.debug(f'Element path live: {ep_live}')
        ep_source = _rebase_element_path_to_origin_source(ep_live)
        logger.debug(f'Element path source: {ep_source}')
        message = 'ep_source is none' if ep_source is None else f'ep_source: {_element_path_lbl(ep_source)}'
        logger.warning(message)
        if ep_source is not None:
            _add_component(ep_source, position, self.element_def)
        else:
            logger.warning(message)


def _pretty(node: js.HTMLElement):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)


def _add_component(el_path: ElementPath, position: Position,
                   element_def: ElementDef):
    file = modlib._find_module_path(el_path.class_module)
    old_source = file.read_text()

    path_index = path_to_index(el_path.path)
    add_result = add_component(old_source, el_path.class_name, element_def, path_index, position)

    if isinstance(add_result, AddResult):
        logger.debug(f'write_module_file len={len(add_result.source_code)} el_path={el_path}')
        injector.get(CanvasSelection).current_selection = el_path

        async def write_source_file():
            from wwwpy.server.designer import rpc
            write_res = await rpc.write_module_file(el_path.class_module, add_result.source_code)
            logger.debug(f'write_module_file res={write_res}')

        create_task_safe((write_source_file()))
    elif isinstance(add_result, AddFailed):
        js.alert('Sorry, an error occurred while adding the component.')
        _open_error_reporter_window(
            'Error report data:\n\n' + add_result.exception_report_b64,
            title='Error report add_component - wwwpy'
        )
