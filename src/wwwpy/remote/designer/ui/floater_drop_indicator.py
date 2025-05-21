from __future__ import annotations

import logging

import js

from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.ui._drop_indicator_svg import svg_indicator_for
from wwwpy.common.designer.ui.rect_readonly import RectReadOnly
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.floater import Floater

logger = logging.getLogger(__name__)


class DropIndicatorFloater(Floater, tag_name='wwwpy-drop-indicator-floater'):

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        <style>
            :host {
              position: fixed;
              pointer-events: none;
              //border: 2px solid #4a90e2;
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

    def show(self):
        self.element.style.display = 'block'

    def set_reference_geometry(self, rect: RectReadOnly):
        raise NotImplementedError()

    def set_reference_geometry2(self, rect: RectReadOnly, position: Position):

        bs = 2  # Adjust this value to match the border size in CSS

        r = js.DOMRect.new(rect.x - bs, rect.y - bs, rect.width, rect.height, )

        self.element.style.display = 'block'
        self.element.style.top = f"{r.top}px"
        self.element.style.left = f"{r.left}px"
        self.element.style.width = f"{r.width}px"
        self.element.style.height = f"{r.height}px"

        sr = self.element.shadowRoot
        while sr.children.length > 1:  # leave style element
            sr.children[1].remove()

        svg = svg_indicator_for(r.width + bs * 2, r.height + bs * 2, position)
        fragment = js.document.createRange().createContextualFragment(svg)
        sr.appendChild(fragment)


def compute_xy(W, H):
    import math
    k = (1 - 1 / math.sqrt(3)) / 2
    return round(W * k, 9), round(H * k)


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
    # return _svg_at_begin
    return _svg_at_end


# language=html
_svg_at_begin = f"""
<svg style='width: 200px ; height: 200px;' viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Main diagonal line (arrow body) - shorter -->
        <line x1="70" y1="70" x2="0" y2="0" stroke-width="6" stroke="black">
            <animate
                    attributeName="stroke"
                    values="black;white;black"
                    dur="1.5s"
                    repeatCount="indefinite"/>
        </line>

        <!-- First arrowhead segment -->
        <line x1="-3" y1="0" x2="47" y2="0" stroke-width="6" stroke="black">
            <animate
                    attributeName="stroke"
                    values="black;white;black"
                    dur="1.5s"
                    repeatCount="indefinite"/>
        </line>

        <!-- Second arrowhead segment -->
        <line x1="0" y1="-3" x2="0" y2="47" stroke-width="6" stroke="black">
            <animate
                    attributeName="stroke"
                    values="black;white;black"
                    dur="1.5s"
                    repeatCount="indefinite"/>
        </line>
        <animateTransform
                attributeName="transform"
                type="translate"
                values="3,3; 10,10; 3,3"
                dur="1s"
                repeatCount="indefinite"
                additive="sum"/>
    </g>
</svg>
"""
# language=html
_svg_at_end = f"""

<svg  style='width: 200px ; height: 200px;' viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Main diagonal line (arrow body) - shorter -->
        <line x1="30" y1="30" x2="100" y2="100" stroke-width="6" stroke="black">
            <animate
                    attributeName="stroke"
                    values="black;white;black"
                    dur="1.5s"
                    repeatCount="indefinite"/>
        </line>

        <!-- First arrowhead segment (horizontal) -->
        <line x1="53" y1="100" x2="103" y2="100" stroke-width="6" stroke="black">
            <animate
                    attributeName="stroke"
                    values="black;white;black"
                    dur="1.5s"
                    repeatCount="indefinite"/>
        </line>

        <!-- Second arrowhead segment (vertical) -->
        <line x1="100" y1="53" x2="100" y2="103" stroke-width="6" stroke="black">
            <animate
                    attributeName="stroke"
                    values="black;white;black"
                    dur="1.5s"
                    repeatCount="indefinite"/>
        </line>
        <animateTransform
                attributeName="transform"
                type="translate"
                values="-3,-3; -10,-10; -3,-3"
                dur="1s"
                repeatCount="indefinite"
                additive="sum"/>
    </g>
</svg>
"""
