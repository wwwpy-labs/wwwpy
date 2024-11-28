from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, List, Callable

import js
from js import document, console, ResizeObserver
from pyodide.ffi import create_proxy
from pyodide.ffi.wrappers import add_event_listener, remove_event_listener

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from typing import NamedTuple
import logging

logger = logging.getLogger(__name__)


class Geometry(NamedTuple):
    top: int
    left: int
    width: int
    height: int


class WindowComponent(wpc.Component, tag_name='wwwpy-window'):
    window_div: wpc.HTMLElement = wpc.element()
    window_title_div: wpc.HTMLElement = wpc.element()
    client_x = 0
    client_y = 0
    css_border = 2  # 1px border on each side, so we need to subtract 2px from width and height
    geometry_change_listeners: List[Callable[[], None]] = []

    def root_element(self):
        return self.element.shadowRoot

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>
.window {
  z-index: 100000;  
  background-color: black;
  border: 1px solid #d3d3d3;
  resize: both;  
  overflow: hidden;
  position: absolute;  /* Changed from 'relative' to 'absolute' */
  display: flex;
  flex-direction: column;
}

.window-title {
  padding: 10px;
  cursor: move;
  z-index: 1001;
  background-color: #2196F3;
  color: #fff;
  touch-action: none;
}

.window-body {
  overflow: auto;
}
</style>        
<div data-name="window_div" class='window'>
    <div data-name="window_title_div" class='window-title' >
        <slot name='title'>slot=title</slot>
    </div>
   <div class='window-body'>
        <slot>slot=default</slot>
    </div>    
</div> 
"""
        self.client_x = 0
        self.client_y = 0

        self._pointermove_proxy = create_proxy(self._pointermove)
        self._pointerup_proxy = create_proxy(self._pointerup)

        def on_resize(entries, observer):
            self._on_geometry_change()

        resize_observer = ResizeObserver.new(create_proxy(on_resize))
        resize_observer.observe(self.window_div)

    def _on_geometry_change(self):
        for listener in self.geometry_change_listeners:
            listener()

    def window_title_div__pointerdown(self, e: js.PointerEvent):
        self._move_start(e)

    def _pointermove(self, event: js.PointerEvent):
        x = event.clientX
        y = event.clientY
        delta_x = self.client_x - x
        delta_y = self.client_y - y
        self.client_x = x
        self.client_y = y

        # Get current 'left' and 'top' from style, defaulting to 0 if not set
        current_left = float(self.window_div.style.left.rstrip('px')) if self.window_div.style.left else 0
        current_top = float(self.window_div.style.top.rstrip('px')) if self.window_div.style.top else 0

        new_left = current_left - delta_x
        new_top = current_top - delta_y

        self.set_position(f'{new_left}px', f'{new_top}px')
        self._on_geometry_change()

    def _move_start(self, e: js.PointerEvent):
        e.preventDefault()
        self.client_x = e.clientX
        self.client_y = e.clientY

        # Capture the pointer to ensure consistent event flow
        self.window_title_div.setPointerCapture(e.pointerId)

        # Add event listeners for pointermove and pointerup
        self.window_title_div.addEventListener('pointermove', self._pointermove_proxy)
        self.window_title_div.addEventListener('pointerup', self._pointerup_proxy)

    def _pointerup(self, event: js.PointerEvent):
        # Remove the event listeners for pointermove and pointerup
        self.window_title_div.removeEventListener('pointermove', self._pointermove_proxy)
        self.window_title_div.removeEventListener('pointerup', self._pointerup_proxy)

        # Release the pointer capture
        self.window_title_div.releasePointerCapture(event.pointerId)

    def geometry(self) -> Geometry:
        t = self.window_div
        res = Geometry(
            t.offsetTop,
            t.offsetLeft,
            t.offsetWidth - self.css_border,
            t.offsetHeight - self.css_border
        )
        return res

    def set_geometry(self, geometry_tuple):
        top, left, width, height = geometry_tuple
        self.set_position(f"{left}px", f"{top}px")
        self.set_size(f"{height}px", f"{width}px")

    def set_position(self, left: str | None = None, top: str | None = None):
        if top:
            logger.info(f'set_position: top={top}')
            top_check = float(top.removesuffix('px'))
            if top_check < 0:
                top = '0px'
            self.window_div.style.top = top
        if left:
            g = self.geometry()
            left_check = float(left.removesuffix('px'))
            if (left_check + g.width) > 30:
                self.window_div.style.left = left

    def set_size(self, height: str | None = None, width: str | None = None):
        if height:
            self.window_div.style.height = height
        if width:
            self.window_div.style.width = width

    def acceptable_geometry(self) -> bool:
        g = self.geometry()
        return g.width > 100 and g.height > 100 and g.top > 0 and g.left > 0


@dataclass
class WindowResult:
    window: WindowComponent

    @property
    def element(self):
        return self.window.element


def new_window(title: str, closable=True) -> WindowResult:
    win = WindowComponent()
    # language=html
    ct = ClosableTitle()
    ct.element.setAttribute('slot', 'title')
    ct.title.innerHTML = title
    ct.close.onclick = lambda ev: win.element.remove()
    win.element.append(ct.element)
    if not closable:
        ct.close.style.display = 'none'
    return WindowResult(win)


class ClosableTitle(wpc.Component):
    title: js.HTMLElement = wpc.element()
    close: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = f"""
<div style="display: flex; justify-content: center; align-items: center;">
    <span data-name='title' style="flex-grow: 1; text-align: center;">No title</span>&nbsp;
    <button data-name="close" style="cursor:pointer;">X</button>
</div> """
