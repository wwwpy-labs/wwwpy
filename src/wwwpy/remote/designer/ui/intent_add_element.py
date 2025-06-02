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
from wwwpy.common.injectorlib import injector
from wwwpy.remote.designer.ui.floater_drop_indicator import DropIndicatorFloater
from wwwpy.remote.designer.ui.intent import Intent
from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)

_tool = DropIndicatorFloater()
_tool.transition = True


@dataclass
class AddElementIntent(Intent):  # todo rename InsertElementIntent
    element_def: ElementDefBase = None
    add_element: callable = field(default_factory=lambda: _add_component)

    def __post_init__(self):
        self._tool = _tool

    def on_selected(self):
        pass

    def on_deselected(self):
        self._tool.hide()

    def on_hover(self, locator_event: LocatorEvent):
        assert isinstance(locator_event, LocatorEvent), f'Expected LocatorEvent, got {type(locator_event)}'
        tool = self._tool
        if self._is_recursive(locator_event):
            logger.debug(f'Ignoring hover on {locator_event} because it is recursive')
            tool.hide()
            return
        if not tool.element.isConnected:
            js.document.body.appendChild(tool.element)
        tool.set_reference_geometry2(
            locator_event.main_element.getBoundingClientRect(),
            locator_event.position()
        )
        tool.show()

    def on_submit(self, locator_event: LocatorEvent) -> bool:
        if self._is_recursive(locator_event):
            logger.debug(f'Ignoring submit on {locator_event} because it is recursive')
            self._tool.hide()
            return False
        self.add_element(locator_event.locator, locator_event.position(), self.element_def)
        self._tool.hide()
        return True

    def _is_recursive(self, locator_event: LocatorEvent) -> bool:
        rec = locator_event.locator.class_full_name == self.element_def.python_type
        logger.debug(
            f'Recursive: {rec} {locator_event.locator.class_full_name} is recursive against {self.element_def.python_type}')
        return rec


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
