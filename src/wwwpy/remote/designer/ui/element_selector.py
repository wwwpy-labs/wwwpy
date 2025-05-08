from __future__ import annotations

import logging

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.common.designer.ui.rect_readonly import RectReadOnly
from wwwpy.remote import dict_to_js, dict_to_py
from wwwpy.remote.designer.ui.tool_component import Tool
from wwwpy.remote.designer.ui.tool_selection_indicator import SelectionIndicatorTool
from wwwpy.remote.jslib import is_contained, AnimationFrameTracker

logger = logging.getLogger(__name__)


# logger.setLevel(logging.DEBUG)


class ElementSelector(wpc.Component, tag_name='element-selector'):
    selection_indicator: SelectionIndicatorTool = wpc.element()
    action_band: ActionBandTool = wpc.element()

    # _eventbus: EventBus = inject()

    def init_component(self):
        # Existing code remains the same
        self.element.attachShadow(dict_to_js({'mode': 'open'}))

        # language=html
        self.element.shadowRoot.innerHTML = """
        <selection-indicator-tool data-name="selection_indicator"></selection-indicator-tool>
        <action-band-tool data-name="action_band"></action-band-tool>
        """
        self._selected_element: js.HTMLElement | None = None
        self._last_position = None
        self._update_count = 0
        self._animation_frame_tracker = AnimationFrameTracker(self._on_animation_frame)

    def connectedCallback(self):
        has_py_comp = hasattr(self.element, '_python_component')
        logger.debug(f'has_py_comp: {has_py_comp}')

    def disconnectedCallback(self):
        self._animation_frame_tracker.stop()

    def is_selectable(self, element) -> bool:
        ok = not is_contained(element, self.element)
        return ok

    def set_selected_element(self, element):
        if element is not None and not self.is_selectable(element):
            raise ValueError(f'Element is not selectable `{dict_to_py(element)}`')

        if self._selected_element == element:
            return

        self._animation_frame_tracker.stop()
        self._selected_element = element
        self._last_position = None

        if element:
            self._animation_frame_tracker.start()
        else:
            self.selection_indicator.hide()
            self.action_band.hide()

    def get_selected_element(self):
        return self._selected_element

    def _on_animation_frame(self, timestamp):
        rect = self._selected_element.getBoundingClientRect()
        rect_tup = (rect.top, rect.left, rect.width, rect.height)
        if self._last_position == rect_tup:
            return

        skip_transition = self._last_position is not None

        self._update_count += 1
        logger.debug(f'update_highlight: {self._update_count} skip_transition: {skip_transition}')

        self.selection_indicator.transition = not skip_transition

        for t in [self.selection_indicator, self.action_band]:
            t: Tool
            t.set_reference_geometry(rect)

        self._last_position = rect_tup


class WeirdSelectionIndicatorTool(wpc.Component, Tool, tag_name='weird-selection-indicator-tool'):

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        <style>
            :host {
              position: fixed;
              pointer-events: none;
              border: 2px solid #4a90e2;
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

    def set_reference_geometry(self, rect: RectReadOnly):
        bs = 2  # Adjust this value to match the border size in CSS

        r = js.DOMRect.new(rect.x - bs, rect.y - bs, rect.width, rect.height, )
        # r = rect

        self.element.style.display = 'block'
        self.element.style.top = f"{r.top}px"
        self.element.style.left = f"{r.left}px"
        self.element.style.width = f"{r.width}px"
        self.element.style.height = f"{r.height}px"

        sr = self.element.shadowRoot
        while sr.children.length > 1:
            sr.children[1].remove()

        x, y = compute_xy(rect.width, rect.height)
        fragment = js.document.createRange().createContextualFragment(
            create_svg(rect.width, rect.height, x, y, 'inner'))
        sr.appendChild(fragment)


def compute_xy(W, H):
    import math
    k = (1 - 1 / math.sqrt(3)) / 2
    return round(W * k, 9), round(H * k)


class ActionBandTool(wpc.Component, Tool, tag_name='action-band-tool'):
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


def create_svg(w, h, x, y, pulse_option) -> str:
    """Create SVG string based on parameters."""
    # Validate to ensure inner rectangle has positive dimensions
    if x * 2 >= w or y * 2 >= h:
        return f'<text x="10" y="30" fill="red">Error: Inset values too large for the given width/height</text>'

    # Calculate inner rectangle dimensions
    inner_width = w - 2 * x
    inner_height = h - 2 * y

    # Determine which parts should pulse
    top_class, left_class, bottom_class, right_class, inner_class = [''] * 5

    pulse = 'class="pulse" stroke="cyan"'
    if pulse_option == "top_left":
        top_class, left_class = pulse, pulse
    elif pulse_option == "bottom_right":
        bottom_class, right_class = pulse, pulse
    elif pulse_option == "inner":
        inner_class = pulse

    # Create SVG string with the CSS classes for animation
    return f'''<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">
            <!-- Outer rectangle segments -->
            <line x1="0" y1="0" x2="{w}" y2="0" stroke="blue" stroke-width="2" {top_class} />
            <line x1="0" y1="0" x2="0" y2="{h}" stroke="blue" stroke-width="2" {left_class} />
            <line x1="0" y1="{h}" x2="{w}" y2="{h}" stroke="blue" stroke-width="2" {bottom_class} />
            <line x1="{w}" y1="0" x2="{w}" y2="{h}" stroke="blue" stroke-width="2" {right_class} />

            <!-- Inner rectangle -->
            <rect x="{x}" y="{y}" width="{inner_width}" height="{inner_height}" fill="none" stroke="red" stroke-width="2" {inner_class} />

            <!-- Line connecting bottom-left corners -->
            <line x1="0" y1="{h}" x2="{x}" y2="{h - y}" stroke="green" stroke-width="2" />

            <!-- Line connecting top-right corners -->
            <line x1="{w}" y1="0" x2="{w - x}" y2="{y}" stroke="purple" stroke-width="2" />
        </svg>'''
