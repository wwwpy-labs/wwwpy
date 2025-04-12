from __future__ import annotations

import logging
from collections.abc import Callable

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js, dict_to_py
from wwwpy.remote.jslib import is_contained

logger = logging.getLogger(__name__)


class ElementSelector(wpc.Component, tag_name='element-selector'):
    highlight_overlay: HighlightOverlay = wpc.element()
    toolbar_button: ToolbarButton = wpc.element()

    # _eventbus: EventBus = inject()

    def init_component(self):
        # Existing code remains the same
        self.element.attachShadow(dict_to_js({'mode': 'open'}))

        # language=html
        self.element.shadowRoot.innerHTML = """
        <highlight-overlay data-name="highlight_overlay"></highlight-overlay>
        <toolbar-button data-name="toolbar_button"></toolbar-button>
        """
        self.last_rect_tuple = None
        self.toolbar_element = self.toolbar_button.element
        self._selected_element: js.HTMLElement | None = None

        self._window_monitor = WindowMonitor(lambda: self._selected_element is not None)
        self._window_monitor.listeners.append(lambda: self.update_highlight_no_transitions())
        self.highlight_overlay.transition = True
        # Initialize MutationObserver instead of ResizeObserver
        self._observer = None

    def connectedCallback(self):
        has_py_comp = hasattr(self.element, '_python_component')
        logger.debug(f'has_py_comp: {has_py_comp}')
        self._window_monitor.install()

    def _on_element_mutate(self, mutations, observer):
        """Called when the observed element's attributes change (size or position)"""
        logger.debug(f'on_element_mutate: {len(mutations)} mutations')
        self.update_highlight()

    def disconnectedCallback(self):
        self._window_monitor.uninstall()
        # Clean up MutationObserver
        if self._observer and self._selected_element:
            self._observer.disconnect()
            self._observer = None

    def is_selectable(self, element) -> bool:
        ok = not is_contained(element, self.element)
        return ok

    def set_selected_element(self, element):
        if element is not None and not self.is_selectable(element):
            raise ValueError(f'Element is not selectable `{dict_to_py(element)}`')

        if self._selected_element == element:
            return

        # Clean up previous observer
        if self._observer and self._selected_element:
            self._observer.disconnect()

        self._selected_element = element

        # Setup new observer for the selected element
        if element:
            if not self._observer:
                self._observer = js.MutationObserver.new(create_proxy(self._on_element_mutate))
            # Observe attribute changes (style changes will affect size and position)
            self._observer.observe(element, dict_to_js({
                'attributes': True,
                'attributeFilter': ['style', 'class']
            }))

        self.update_highlight()

    def get_selected_element(self):
        return self._selected_element

    def update_highlight_no_transitions(self):
        self.highlight_overlay.transition = False
        self.update_highlight()
        self.highlight_overlay.transition = True

    def update_highlight(self):
        if not self._selected_element:
            self.highlight_overlay.hide()
            self.toolbar_button.hide()
            return

        rect = self._selected_element.getBoundingClientRect()
        self.last_rect_tuple = (rect.top, rect.left, rect.width, rect.height)

        self.highlight_overlay.show(rect)
        self.toolbar_button.show(rect)


class WindowMonitor:

    def __init__(self, enable_notify: callable):
        self._enable_notify = enable_notify
        self.listeners: list[Callable] = []
        self._raf_id = None

    def install(self):
        js.window.addEventListener('resize', create_proxy(self._handle_event))
        js.window.addEventListener('scroll', create_proxy(self._handle_event), dict_to_js({'passive': True}))

    def uninstall(self):
        js.window.removeEventListener('resize', create_proxy(self._handle_event))
        js.window.removeEventListener('scroll', create_proxy(self._handle_event))

        # todo remove
        if self._raf_id is not None:
            js.window.cancelAnimationFrame(self._raf_id)
            self._raf_id = None

    async def _handle_event(self, event=None):
        if not self._enable_notify():
            return

        self._fire_notify()
        # if self._raf_id is not None:
        #     js.window.cancelAnimationFrame(self._raf_id)

        # def update_on_animation_frame(event):
        #     self._fire_notify()
        #     self._raf_id = None

        # self._raf_id = js.window.requestAnimationFrame(create_proxy(update_on_animation_frame))

    def _fire_notify(self):
        if not self._enable_notify():
            return
        for listener in self.listeners:
            try:
                listener()
            except Exception as e:
                logger.error(f"Error in listener: {e}")


class HighlightOverlay(wpc.Component, tag_name='highlight-overlay'):

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        <style>
            :host {
              position: fixed;
              pointer-events: none;
              border: 2px solid #4a90e2;
              background-color: rgba(74, 144, 226, 0.1);
              z-index: 200000;
              display: none;
            } 
        </style>      
        """

    @property
    def transition(self) -> bool:
        return self.element.style.transition != 'none'

    @transition.setter
    def transition(self, value: bool):
        if value:
            self.element.style.transition = 'all 0.2s ease'
        else:
            self.element.style.transition = 'none'

    @property
    def visible(self) -> bool:
        return self.element.style.display == 'block'

    def hide(self):
        self.element.style.display = 'none'

    def show(self, rect: js.DOMRect):
        bs = 2  # Adjust this value to match the border size in CSS

        rect = js.DOMRect.new(rect.x - bs, rect.y - bs, rect.width, rect.height, )

        self.element.style.display = 'block'
        self.element.style.top = f"{rect.top}px"
        self.element.style.left = f"{rect.left}px"
        self.element.style.width = f"{rect.width}px"
        self.element.style.height = f"{rect.height}px"


# this class is an extraction  of the toolbar above (refactoring)
class ToolbarButton(wpc.Component, tag_name='toolbar-button'):
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
            {'label': 'Delete', 'icon': '🗑️'}
        ]

        for data in button_data:
            button = js.document.createElement('button')
            button.setAttribute('aria-label', data['label'])
            button.setAttribute('title', data['label'])
            button.textContent = data['icon']

            # Create a proxy function to handle the click event
            def create_button_click_handler(action_label):
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

                return button_click_handler

            # Add event listener with the proxy function
            button.addEventListener('click', create_proxy(create_button_click_handler(data['label'])))
            self.element.shadowRoot.appendChild(button)

    def _handle_click(self, event):
        event.stopPropagation()

    def hide(self):
        self.element.style.display = 'none'

    def show(self, rect):
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
