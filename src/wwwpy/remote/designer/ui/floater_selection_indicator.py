from __future__ import annotations

import js

from wwwpy.common.designer.ui.rect_readonly import RectReadOnly
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.floater import Floater


class SelectionIndicatorFloater(Floater, tag_name='selection-indicator-floater'):

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

    def set_reference_geometry(self, rect: RectReadOnly):
        bs = 2  # Adjust this value to match the border size in CSS

        rect = js.DOMRect.new(rect.x - bs, rect.y - bs, rect.width, rect.height, )

        self.element.style.display = 'block'
        self.element.style.top = f"{rect.top}px"
        self.element.style.left = f"{rect.left}px"
        self.element.style.width = f"{rect.width}px"
        self.element.style.height = f"{rect.height}px"
