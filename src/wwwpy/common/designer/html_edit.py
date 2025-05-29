"""This module contains the HTML string manipulator functions."""
from __future__ import annotations

from enum import Enum
from html import escape

from wwwpy.common.designer import html_locator
from wwwpy.common.designer.html_locator import NodePath, IndexPath, check_node_path


class Position(str, Enum):
    afterbegin = 'afterbegin'  # inside
    beforeend = 'beforeend'  # inside
    beforebegin = 'beforebegin'
    afterend = 'afterend'


def html_add(html: str, add: str, node_path: NodePath, position: Position) -> str:
    """This function adds an HTML piece to the specified position in the HTML string."""

    start, end = html_locator.locate_span(html, node_path)

    index = start if position == Position.beforebegin else end

    return html[:index] + add + html[index:]


def html_add_indexed(html: str, add: str, index_path: IndexPath, position: Position) -> str:
    check_node_path(index_path)
    """This function adds an HTML piece to the specified position in the HTML string."""

    start, end = html_locator.locate_span_indexed(html, index_path)

    if position == Position.beforebegin:
        index = start
    elif position == Position.afterend:
        index = end
    elif position == Position.afterbegin:
        # Insert just after the opening tag
        node = html_locator.locate_node_indexed(html, index_path)
        if node is None or node.content_span is None:
            return html
        index = node.content_span[0]
    elif position == Position.beforeend:
        # Insert just before the closing tag
        node = html_locator.locate_node_indexed(html, index_path)
        if node is None or node.content_span is None:
            return html
        index = node.content_span[1]
    else:
        raise ValueError(f"Unknown position: {position}")

    return html[:index] + add + html[index:]


def html_edit(html: str, edit: str, node_path: NodePath) -> str:
    """This function edits the HTML string at the specified path."""
    start, end = html_locator.locate_span(html, node_path)

    return html[:start] + edit + html[end:]


def html_edit_indexed(html: str, edit: str, index_path: NodePath) -> str:
    check_node_path(index_path)
    """This function edits the HTML string at the specified path."""
    start, end = html_locator.locate_span_indexed(html, index_path)

    return html[:start] + edit + html[end:]


def html_attribute_set(html: str, node_path: NodePath, attr_name: str, attr_value: str | None) -> str:
    """This function sets an attribute of the specified node in the HTML string.
    When the value is None, the attribute value is remove entirely"""

    node = html_locator.locate_node(html, node_path)
    if node is None:
        print(f'node not found at path={node_path} in html=```{html}```')
        return html

    cst_attr = node.cst_attribute(attr_name)
    attr_present = cst_attr is not None
    value_present = attr_present and cst_attr.value_span is not None
    spacer = ' ' if not attr_present else ''
    sep = '"' if not value_present else html[cst_attr.value_span[0]]

    value_part = '' if attr_value is None else '=' + sep + escape(attr_value) + sep

    x = cst_attr.name_span[0] if attr_present else node.attr_span[1]
    y = cst_attr.value_span[1] if value_present else (x if not attr_present else cst_attr.name_span[1])
    left = html[:x]
    right = html[y:]

    return left + spacer + attr_name + value_part + right


def html_attribute_remove(html: str, node_path: NodePath, attr_name: str) -> str:
    node = html_locator.locate_node(html, node_path)
    if node is None:
        return html

    cst_attr = node.cst_attribute(attr_name)
    if cst_attr is None:
        return html

    if len(node.attributes) == 1:
        x = node.attr_span[0]
        y = node.attr_span[1]
        return html[:x] + html[y:]


    value_present = cst_attr.value_span is not None
    x = cst_attr.name_span[0]
    y = cst_attr.value_span[1] if value_present else cst_attr.name_span[1]

    left = html[:x]
    right = html[y:]

    left = left.rstrip()
    right = right.lstrip()

    is_last_attr = cst_attr == node.attributes_list[-1]
    space = '' if is_last_attr else ' '

    return left + space + right


def html_content_set(html: str, node_path: NodePath, value: str) -> str | None:
    """This function sets the content of the specified node in the HTML string."""

    node = html_locator.locate_node(html, node_path)
    if node is None:
        raise Exception(f'node not found at path={node_path} in html=```{html}```')

    if node.content_span is None:
        raise Exception(f'node is a void tag at path={node_path} in html=```{html}```')

    x, y = node.content_span
    left = html[:x]
    right = html[y:]
    return left + value + right


def html_remove_indexed(html: str, index_path: IndexPath) -> str:
    check_node_path(index_path)
    """This function removes the node specified by the path from the HTML string."""

    node = html_locator.locate_node_indexed(html, index_path)
    if node is None:
        return html

    x, y = node.span
    left = html[:x]
    right = html[y:]
    return left + right
