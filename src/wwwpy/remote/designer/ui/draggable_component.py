from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, List, Callable

import js
from js import document, console, ResizeObserver
from pyodide.ffi import create_proxy
from pyodide.ffi.wrappers import add_event_listener, remove_event_listener

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js


class DraggableComponent(wpc.Component, tag_name='wwwpy-draggable-component'):
    window_div: wpc.HTMLElement = wpc.element()
    window_title_div: wpc.HTMLElement = wpc.element()
    client_x = 0
    client_y = 0
    css_border = 2  # 1px border on each side, so we need to subtract 2px from width and height
    geometry_change_listeners: List[Callable[[], None]] = []

    def root_element(self):
        return self.shadow

    def init_component(self):
        self.shadow = self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.shadow.innerHTML = """
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
}

.window-body {
  overflow: auto;
}
</style>        
<div data-name="window_div" class='window'>
    <div  data-name="window_title_div" class='window-title' >
        <slot name='title' >slot=title</slot>
    </div>
   <div class='window-body'>
        <slot>slot=default</slot>
    </div>    
</div> 
"""
        self.client_x = 0
        self.client_y = 0
        tb = self.window_div

        def tb_print(*args):
            console.log(f'offsets of window_div: {self.geometry()}')

        tb.print = tb_print

        def on_resize(entries, observer):
            tb.print()
            self._on_geometry_change()

        resize_observer = ResizeObserver.new(create_proxy(on_resize))
        resize_observer.observe(self.window_div)

    def _on_geometry_change(self):
        for listener in self.geometry_change_listeners:
            listener()

    def window_title_div__touchstart(self, e: js.TouchEvent):
        self._move_start(e)

    def window_title_div__mousedown(self, e: js.MouseEvent):
        self._move_start(e)

    def _move_start(self, e: js.MouseEvent | js.TouchEvent):
        e.preventDefault()
        self.client_x = clientX(e)  # e.clientX
        self.client_y = clientY(e)  # e.clientY
        add_event_listener(document, 'mousemove', self._move)
        add_event_listener(document, 'mouseup', self._move_stop)
        add_event_listener(document, 'touchmove', self._move)
        add_event_listener(document, 'touchend', self._move_stop)

    def _move(self, event: js.MouseEvent | js.TouchEvent):
        x = clientX(event)
        y = clientY(event)
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

    def _move_stop(self, event):
        remove_event_listener(document, 'mousemove', self._move)
        remove_event_listener(document, 'mouseup', self._move_stop)
        remove_event_listener(document, 'touchmove', self._move)
        remove_event_listener(document, 'touchend', self._move_stop)

    def geometry(self) -> Tuple[int, int, int, int]:
        t = self.window_div
        return t.offsetTop, t.offsetLeft, (t.offsetWidth - self.css_border), (t.offsetHeight - self.css_border)

    def set_geometry(self, geometry_tuple):
        top, left, width, height = geometry_tuple
        self.set_position(f"{left}px", f"{top}px")
        self.set_size(f"{height}px", f"{width}px")

    def set_position(self, left: str | None = None, top: str | None = None):
        if top:
            self.window_div.style.top = top
        if left:
            self.window_div.style.left = left

    def set_size(self, height: str | None = None, width: str | None = None):
        if height:
            self.window_div.style.height = height
        if width:
            self.window_div.style.width = width

    def acceptable_geometry(self) -> bool:
        top, left, width, height = self.geometry()
        return width > 100 and height > 100


def clientX(event: js.MouseEvent | js.TouchEvent):
    #   var top = e.clientY || e.targetTouches[0].pageY;
    # return event.clientX if hasattr(event, 'clientX') else event.targetTouches[0].clientX
    if hasattr(event, 'targetTouches'):
        return list(event.targetTouches)[0].clientX
    return event.clientX


def clientY(event: js.MouseEvent | js.TouchEvent):
    return event.clientY if hasattr(event, 'clientY') else list(event.targetTouches)[0].clientY


@dataclass
class WindowResult:
    window: DraggableComponent

    @property
    def element(self):
        return self.window.element


def new_window(title: str, closable=True) -> WindowResult:
    win = DraggableComponent()
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
    <span data-name='title' style="flex-grow: 1; text-align: center;"></span>&nbsp;
    <button data-name="close" style="cursor:pointer;">X</button>
</div> """
