from __future__ import annotations

import logging

import js
from js import Array, document

from wwwpy.common.designer.html_locator import Node
from wwwpy.common.designer.locator_lib import Locator, Origin
from wwwpy.remote.component import get_component
from wwwpy.remote.jslib import is_instance_of

logger = logging.getLogger(__name__)


def locator_from(element: js.Element) -> Locator | None:
    """Returns an instance of ElementPath that describes the path to the element"""

    # Start building the path
    path = []
    current = element

    while current:
        # Check if we've reached a component
        component = get_component(current)
        if component:
            clazz = component.__class__
            # We found the component, return the path
            return Locator(clazz.__module__, clazz.__name__, path, Origin.live)

        # Reached document body without finding a component
        if current == document.body:
            return None

        # Handle shadow root - move to host element
        if is_instance_of(current, js.ShadowRoot):
            current = current.host
            continue

        # Get the parent to determine next step
        parent = current.parentNode
        if not parent:
            return None

        # Add the current node to the path
        add_node_to_path(current, parent, path)

        if hasattr(current, "assignedSlot") and current.assignedSlot:
            add_node_to_path(parent, parent.parentNode, path)
            current = parent.parentNode
            continue

        # Move up to parent for next iteration
        current = parent

    return None


def add_node_to_path(node, parent, path):
    """Helper to add a node to the path with its attributes and position"""
    child_index = Array.prototype.indexOf.call(parent.children, node) if parent else -1
    attributes = {attr.name: attr.value for attr in node.attributes}
    path.insert(0, Node(node.tagName.lower(), child_index, attributes))
