from __future__ import annotations

import logging
from typing import TypeVar, Type

import js

from wwwpy.common.designer.ui.rect_readonly import rect_xy_center
from wwwpy.remote.component import get_component, Component

logger = logging.getLogger(__name__)
ComponentType = TypeVar('ComponentType', bound=Component)


def global_instance(cls: Type[ComponentType], id_name: str | None = None) -> ComponentType:
    """
    Creates or retrieves a global instance of the given component class.

    Args:
        cls: The component class to instantiate
        id_name: Optional ID for the element, defaults to 'id_' + tag_name

    Returns:
        An instance of the specific component class
    """
    if id_name is None:
        id_name = 'id_' + cls.component_metadata.tag_name
    tag_name = cls.component_metadata.tag_name
    element = single_tag_instance(tag_name, id_name)
    comp = get_component(element)
    assert isinstance(comp, cls), f'Expected {cls}, tag_name={tag_name}, got {comp}, from element {element}'
    return comp


def single_tag_instance(tag_name: str, global_id: str, where=js.document.body) -> js.HTMLElement:
    """Get or create a single tag instance with the given ID."""
    ele = js.document.getElementById(global_id)
    if ele is None:
        ele = js.document.createElement(tag_name)
        ele.id = global_id
        where.appendChild(ele)
    return ele


def ensure_tag_instance(tag_name: str, global_id: str, where=js.document.body) -> js.HTMLElement:
    """Get or create a single tag instance with the given ID."""
    ele = js.document.getElementById(global_id)
    if ele is None:
        logger.debug(f'Creating new element {tag_name} with id {global_id}')
        ele = js.document.createElement(tag_name)
        ele.id = global_id
        where.appendChild(ele)
    return ele


def element_xy_center(element: js.Element) -> tuple[float, float]:
    """Get the center x and y coordinates of the given element relative to the page."""
    rect = element.getBoundingClientRect()
    return rect_xy_center(rect)
