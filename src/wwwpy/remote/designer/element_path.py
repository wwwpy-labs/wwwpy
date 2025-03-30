from __future__ import annotations

import logging

import js
from js import Array, Element, document

from wwwpy.common.designer.element_path import ElementPath, Origin
from wwwpy.common.designer.html_locator import Node
from wwwpy.remote.component import get_component

logger = logging.getLogger(__name__)


def element_path(element: Element) -> ElementPath | None:
    """Returns an instance of  """

    path = []
    while element:
        if is_instance_of(element, js.ShadowRoot):
            element = element.host
        component = get_component(element)
        if component:
            clazz = component.__class__
            return ElementPath(clazz.__module__, clazz.__name__, path, Origin.live)
        if element == document.body:
            return None

        parent = element.parentNode
        child_index = Array.prototype.indexOf.call(parent.children, element) if parent else -1
        attributes = {attr.name: attr.value for attr in element.attributes}
        path.insert(0, Node(element.tagName.lower(), child_index, attributes))
        element = parent

    return None


_instanceof = js.eval('(i,t) => i instanceof t')


def is_instance_of(instance, js_type):
    return _instanceof(instance, js_type)
