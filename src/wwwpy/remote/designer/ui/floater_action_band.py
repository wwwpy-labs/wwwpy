from __future__ import annotations

import logging

import js
from pyodide.ffi import create_proxy

from wwwpy.common.designer.ui.rect_readonly import RectReadOnly
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.design_aware import DesignAware
from wwwpy.remote.designer.ui.floater import Floater
from wwwpy.remote.designer.ui.locator_event import LocatorEvent
from wwwpy.remote.jslib import is_contained

logger = logging.getLogger(__name__)


class _DesignAware(DesignAware):

    def is_selectable_le(self, locator_event: LocatorEvent) -> bool | None:
        def is_container(element: js.Element) -> bool:
            return element.tagName.lower() == ActionBandFloater.component_metadata.tag_name.lower()

        is_cont = is_contained(locator_event.main_element, is_container)
        logger.debug(f'is_selectable_le is_contained inside ActionBandFloater:{is_cont} ')
        if is_cont:
            return False
        return None


_design_aware = _DesignAware()


def extension_point_register():
    DesignAware.EP_REGISTRY.register(_design_aware)


def extension_point_unregister():
    DesignAware.EP_REGISTRY.unregister(_design_aware)


class ActionBandFloater(Floater, tag_name='action-band-floater'):
    """A component for creating a toolbar button with an icon and label.
    Converted from the JavaScript implementation in selection-scroll-1.html.
    """

    def init_component(self):
        """Initialize the component"""
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        <style>
             :host {
              position: fixed;
              display: none;
              background-color: #333;
              border-radius: 4px;
              padding: 4px;
              z-index: 200001;
              box-shadow: 0 2px 5px rgba(0,0,0,0.2);
              white-space: nowrap;
              min-width: max-content;
              pointer-events: auto;
            }

            button {
              background-color: transparent;
              color: white;
              border: none;
              width: 30px;
              height: 30px;
              border-radius: 3px;
              cursor: pointer;
              margin: 0 2px;
            }

            button:hover {
              background-color: rgba(255,255,255,0.2);
            }
        </style>
        """
        self._toolbar_dimensions = None
        self.toolbar_element = self.element

        button_data = [
            {'label': 'Parent', 'icon': '←'},
            {'label': 'Move up', 'icon': '↑'},
            {'label': 'Move down', 'icon': '↓'},
            {'label': 'Edit', 'icon': '✏️'},
            {'label': 'Delete', 'icon': '🗑️', 'function': _delete_element},
        ]

        for data in button_data:
            button = js.document.createElement('button')
            button.setAttribute('aria-label', data['label'])
            button.setAttribute('title', data['label'])
            button.textContent = data['icon']

            # Create a proxy function to handle the click event
            def create_button_click_handler(action_label, data=data):
                def button_click_handler(e):
                    e.stopPropagation()
                    # Dispatch a custom event when a toolbar button is clicked
                    self.element.dispatchEvent(
                        js.CustomEvent.new('toolbar-action', dict_to_js({
                            'bubbles': True,
                            'composed': True,
                            'detail': {
                                'action': action_label,
                            }
                        }))
                    )
                    fun = data.get('function', None)
                    if fun:
                        fun()
                    else:
                        js.alert(f"Button clicked: {data['label']}")

                return button_click_handler

            # Add event listener with the proxy function
            button.addEventListener('click', create_proxy(create_button_click_handler(data['label'])))
            self.element.shadowRoot.appendChild(button)

    def _handle_click(self, event):
        event.stopPropagation()

    def hide(self):
        self.element.style.display = 'none'

    def set_reference_geometry(self, rect: RectReadOnly):
        # self._toolbar_dimensions = None
        # Only measure the toolbar once initially to avoid layout thrashing
        if not self._toolbar_dimensions:
            self.toolbar_element.style.display = 'block'
            self.toolbar_element.style.visibility = 'hidden'
            self.toolbar_element.style.top = '-9999px'  # Position off-screen for measurement

            # Cache toolbar dimensions
            self._toolbar_dimensions = {
                'width': self.toolbar_element.offsetWidth,
                'height': self.toolbar_element.offsetHeight
            }

        # Use cached dimensions
        toolbar_width = self._toolbar_dimensions['width']
        toolbar_height = self._toolbar_dimensions['height']

        # Position the toolbar at bottom-right
        toolbar_x = rect.right - toolbar_width  # Align right edges
        toolbar_y = rect.bottom + 5  # Add 5px offset

        # Check if the toolbar would go off-screen to the left
        if toolbar_x < 0:
            toolbar_x = rect.left

        # Check if toolbar would go off-screen at the bottom
        if rect.bottom + toolbar_height + 5 > js.window.innerHeight:
            toolbar_y = rect.top - toolbar_height - 5

        self.toolbar_element.style.display = 'block'
        self.toolbar_element.style.visibility = 'visible'
        self.toolbar_element.style.left = f"{toolbar_x}px"
        self.toolbar_element.style.top = f"{toolbar_y}px"


def _delete_element():
    from wwwpy.common.asynclib import create_task_safe
    from wwwpy.common.designer.canvas_selection import CanvasSelection
    from wwwpy.common.designer.code_edit import remove_element
    from wwwpy.common.designer.html_locator import path_to_index
    canvas_selection = injector.get(CanvasSelection)
    el_path = canvas_selection.current_selection
    if not el_path:
        return
    from wwwpy.common import modlib
    file = modlib._find_module_path(el_path.class_module)
    old_source = file.read_text()

    path_index = path_to_index(el_path.path)
    remove_result = remove_element(old_source, el_path.class_name, path_index)
    if not remove_result:
        js.alert('Something went wrong')
        return

    logger.debug(f'write_module_file len={len(remove_result)} el_path={el_path}')

    async def write_source_file():
        from wwwpy.server.designer import rpc
        write_res = await rpc.write_module_file(el_path.class_module, remove_result)
        canvas_selection.current_selection = None
        logger.debug(f'write_module_file res={write_res}')

    create_task_safe((write_source_file()))


def _pretty(node: js.Element):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
