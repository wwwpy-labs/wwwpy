from __future__ import annotations

import logging
from dataclasses import dataclass, field

import js

from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.locator_lib import Locator, Origin
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.component import Component, get_component
from wwwpy.remote.designer.locator_js import locator_from
from wwwpy.remote.jslib import is_instance_of, get_deepest_element

logger = logging.getLogger(__name__)


def default_position_resolver(width: float, height: float, x: float, y: float) -> Position:
    """the x and y coordinates are relative to the top-left corner of the element"""
    from wwwpy.common.designer.ui._drop_indicator_svg import position_for
    return position_for(width, height, x, y)


def find_first_user_component() -> Component | None:
    # todo should exclude wwwpy internal components
    for element in js.document.body.children:
        logger.debug(f'find_first_user_component: checking {_pretty(element)}')
        component = get_component(element)
        if component:
            return component

    return None


@dataclass
class LocatorEvent:
    locator: Locator
    """The origin must be Origin.source"""
    main_element: js.Element
    main_xy: tuple[float, float]
    """The xy coordinates of the main element, relative to the page"""
    secondary_elements: list[js.HTMLElement] = field(default_factory=list)
    position_resolver: callable = field(default=default_position_resolver)

    def __post_init__(self):
        assert self.locator is not None, 'locator must not be None'
        assert self.locator.origin == Origin.source
        assert is_instance_of(self.main_element,
                              js.HTMLElement), f'main_element must be an HTMLElement, got {type(self.main_element)}'

    def position(self) -> Position:
        rect = self.main_element.getBoundingClientRect()
        w, h = rect.width, rect.height
        ax, ay = self.main_xy
        x = ax - rect.left
        y = ay - rect.top
        return self.position_resolver(w, h, x, y)

    @staticmethod
    def from_pointer_event(js_event: js.PointerEvent) -> LocatorEvent | None:
        xy = js_event.clientX, js_event.clientY
        element = get_deepest_element(*xy)
        logger.debug(f'from_pointer_event: {js_event.type} at {xy}, element: {_pretty(element)}')
        if element == js.document.body or element == js.document.documentElement:
            component = find_first_user_component()
            if not component:
                logger.debug('from_pointer_event: no user component found, returning None')
            else:
                element = component.element
        if not element:
            return None
        l = LocatorEvent.from_element(element, xy)
        return l

    @staticmethod
    def from_element(element: js.Element, xy: tuple[float, float] | None = None) -> LocatorEvent | None:
        locator = locator_from(element)
        loc_origin = locator.rebase_to_origin()
        if not loc_origin:
            logger.warning(f'locator returned None for element: {_pretty(element)}')
            return None

        if xy is None:
            xy = element_xy_center(element)

        return LocatorEvent(loc_origin, element, xy)


def _pretty(node: js.Element):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
