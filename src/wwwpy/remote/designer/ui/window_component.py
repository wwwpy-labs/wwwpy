from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, List, Callable

import js
from js import document, console, ResizeObserver
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from typing import NamedTuple
import logging

logger = logging.getLogger(__name__)


class Geometry(NamedTuple):
    left: int
    top: int
    width: int
    height: int


class WindowComponent(wpc.Component, tag_name='wwwpy-window'):
    window_div: wpc.HTMLElement = wpc.element()
    window_title_div: wpc.HTMLElement = wpc.element()
    client_x: int
    client_y: int
    css_border = 2  # 1px border on each side, so we need to subtract 2px from width and height
    geometry_change_listeners: List[Callable[[], None]] = []

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
        # we don't rely on self.window_div.offsetLeft/offsetTop for reading x/y location
        # because they need rendering to be up to date
        self.window_div.style.top = '10px'
        self.window_div.style.left = '20px'
        self._win_move(0, 0)

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

    def _move_start(self, e: js.PointerEvent):
        e.preventDefault()
        self._update_client_xy(e)

        self.window_title_div.setPointerCapture(e.pointerId)

        self.window_title_div.addEventListener('pointermove', self._pointermove_proxy)
        self.window_title_div.addEventListener('pointerup', self._pointerup_proxy)

    def _update_client_xy(self, e):
        self.client_x = e.clientX
        self.client_y = e.clientY

    def _pointermove(self, event: js.PointerEvent):
        self._win_move(self.client_x - event.clientX, self.client_y - event.clientY)
        self._update_client_xy(event)

    def _win_move(self, delta_x, delta_y):
        current_left = float(self.window_div.style.left.rstrip('px'))
        current_top = float(self.window_div.style.top.rstrip('px'))
        new_left = current_left - delta_x
        new_top = current_top - delta_y
        self.set_position(f'{new_left}px', f'{new_top}px')
        self._on_geometry_change()

    def _pointerup(self, event: js.PointerEvent):
        self.window_title_div.removeEventListener('pointermove', self._pointermove_proxy)
        self.window_title_div.removeEventListener('pointerup', self._pointerup_proxy)
        self.window_title_div.releasePointerCapture(event.pointerId)

    def geometry(self) -> Geometry:
        t = self.window_div
        res = Geometry(
            t.offsetLeft,
            t.offsetTop,
            t.offsetWidth - self.css_border,
            t.offsetHeight - self.css_border
        )
        return res

    def set_geometry(self, geometry_tuple: Geometry):
        left, top, width, height = geometry_tuple
        self.set_position(f"{left}px", f"{top}px")
        self.set_size(f"{height}px", f"{width}px")

    def set_position(self, left: str | None = None, top: str | None = None):
        if top:
            top_check = float(top.removesuffix('px'))
            if top_check < 0:
                top = '0px'
            self.window_div.style.top = top
        if left:
            g = self.geometry()
            left_check = float(left.removesuffix('px'))
            if (left_check + g.width) > 30:
                self.window_div.style.left = left
        logger.debug(f'set_position top={top} left={left}')

    def set_size(self, height: str | None = None, width: str | None = None):
        if height:
            self.window_div.style.height = height
        if width:
            self.window_div.style.width = width


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
    ct.close.onpointerdown = lambda e: [e.preventDefault(), e.stopPropagation(), win.element.remove()]
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
