from __future__ import annotations

import js

from wwwpy.common.designer.ui.rect_readonly import RectReadOnly
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.floater import Floater


class WeirdSelectionIndicatorFloater(Floater, tag_name='weird-selection-indicator-floater'):

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
