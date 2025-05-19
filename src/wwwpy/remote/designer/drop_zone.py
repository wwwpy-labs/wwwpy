from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Callable

import js
from js import document, MouseEvent, HTMLElement
from pyodide.ffi import create_proxy

from wwwpy.common.designer.html_edit import Position


@dataclass
class DropZone:
    element: HTMLElement
    position: Position

class DropZoneHover(Protocol):
    """The protocol for the callback function that will be called when the user hovers in/out of a drop zone."""
    def __call__(self, event: DropZone | None) -> None: ...

def _default_extract_target(event: MouseEvent) -> HTMLElement:
    return event.target


def _extract_first_with_data_name(event: MouseEvent) -> HTMLElement:
    ele: js.HTMLElement = event.target
    while ele is not None:
        if ele.hasAttribute('data-name'):
            return ele
        ele = ele.parentElement
    return event.target


# todo refactor to better integrate with toolbox
class _DropZoneSelector:
    def __init__(self, ):
        self._last_zone: DropZone | None = None
        self._accept = None
        self._callback: DropZoneHover | None = None
        self._mousemove_proxy = create_proxy(self._mousemove)
        # todo not under test
        self._whole = False
        self._extract_target = None

    def start_selector(self, callback: DropZoneHover = None,
                       accept: Callable[[DropZone], bool] = None,
                       whole=False,
                       extract_target: Callable[[MouseEvent], HTMLElement] = _extract_first_with_data_name):
        """It starts the process for the user to select a drop zone.
        While moving the mouse, it highlights the drop zones.
        """
        self._callback = callback
        self._accept = accept
        self._whole = whole
        self._extract_target = extract_target
        _ensure_drop_zone_style()
        document.addEventListener('mousemove', self._mousemove_proxy)

    def stop(self) -> DropZone | None:
        """It stops the process of selecting a drop zone.
        It will remove the highlights and the event listener.
        It will return the selected DropZone
        """
        document.removeEventListener('mousemove', self._mousemove_proxy)
        self._remove_marker()
        result = self._last_zone
        return result

    def _mousemove(self, event: MouseEvent):
        position = _calc_position(event)
        element: HTMLElement = self._extract_target(event)
        zone_event = DropZone(element, position)
        accept = True
        if self._accept:
            accept = self._accept(zone_event)
        if not accept:
            zone_event = None

        if self._last_zone != zone_event:
            self._remove_marker()
            self._last_zone = zone_event
            if zone_event is not None:
                # console.log(f'candidate sending zone_event', zone_event.position, zone_event.target)
                if self._whole:
                    element.classList.add(_whole_css_class)
                else:
                    css_class = _beforebegin_css_class if position == Position.beforebegin else _afterend_css_class
                    element.classList.add(css_class)
            if self._callback:
                self._callback(zone_event)
        else:
            pass
            # console.log(f'candidate discarded zone_event: {zone_event}')

    def _remove_marker(self):
        if self._last_zone is not None:
            _remove_class(self._last_zone.element, _beforebegin_css_class)
            _remove_class(self._last_zone.element, _afterend_css_class)
            _remove_class(self._last_zone.element, _whole_css_class)


drop_zone_selector = _DropZoneSelector()

_beforebegin_css_class = 'drop-zone-beforebegin'
_afterend_css_class = 'drop-zone-afterend'
_whole_css_class = 'drop-zone-whole'


def _remove_class(target: HTMLElement, class_name: str):
    target.classList.remove(class_name)
    if target.classList.length == 0:
        target.removeAttribute('class')


def _ensure_drop_zone_style():
    drop_zone_highlight_style = 'drop-zone-highlight-style'
    _ensure_style_element(drop_zone_highlight_style, f"""
    .{_beforebegin_css_class} {{
        box-shadow: -4px -4px 0 green;
        position: relative;
        z-index: 10;
    }}
    .{_afterend_css_class} {{
        box-shadow: 2px 2px 2px 2px green;
        position: relative;
        z-index: 10;
    }}
    .{_whole_css_class} {{
        box-shadow: 0 0 0 2px green;
        position: relative;
        z-index: 10;
    }}
""")


def _ensure_style_element(element_id: str, style_content: str):
    st = document.head.querySelector(f'#{element_id}')
    if st is None:
        st = document.createElement('style')
        st.id = element_id
        document.head.appendChild(st)

    if st.innerHTML != style_content:
        st.innerHTML = style_content


def _calc_position(event: MouseEvent) -> Position:
    element: HTMLElement = event.target
    rect = element.getBoundingClientRect()

    # Calculate the position of the mouse relative to the element
    x = event.clientX - rect.left
    y = rect.height - (event.clientY - rect.top)
    h = rect.height
    w = rect.width
    if w == 0:
        return Position.beforeend
    m = h / w
    y2 = m * x
    res = Position.afterend if y <= y2 else Position.beforebegin
    # console.log(f'x={x}, y={y}, w={w}, h={h} m={m}, y2={y2} res={res}')
    return res
