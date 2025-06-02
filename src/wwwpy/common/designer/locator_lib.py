from __future__ import annotations

import dataclasses
# todo maybe rename to locatorlib.py
import logging
from dataclasses import dataclass
from enum import Enum

from wwwpy.common.designer.html_locator import NodePath, data_name

logger = logging.getLogger(__name__)


class Origin(str, Enum):
    source = 'source'
    """The original html source in the component"""
    live = 'live'
    """The live html in the browser"""


@dataclass()
class Locator:
    """Contains the path to an element relative to a Component.
    This is intended to be serialized"""

    class_module: str
    """The module name of the Component."""
    class_name: str
    """The class name of the Component."""
    path: NodePath
    """The path from the Component (excluded) to the element."""

    origin: Origin

    @property
    def class_full_name(self) -> str:
        return f'{self.class_module}.{self.class_name}'

    @property
    def tag_name(self) -> str:
        """The tag name of the element in lowercase."""
        if len(self.path) == 0:
            return ''
        return self.path[-1].tag_name

    @property
    def data_name(self) -> str | None:
        """The name of the element in the data dictionary."""
        return data_name(self.path)

    def valid(self) -> bool:
        from wwwpy.common.designer import code_strings as cs, html_locator as hl
        html = cs.html_from(self.class_module, self.class_name)
        if not html:
            logger.warning(f'Cannot find html for {self.class_module}.{self.class_name}')
            return False
        span = hl.locate_span(html, self.path)
        if not span:
            logger.warning(f'Cannot locate span for {self.path} in html=`{html}`')
        return span is not None

    def rebase_to_origin(self) -> Locator | None:
        return rebase_to_origin(self)

    def match_component_type(self, component_type) -> bool:
        module = component_type.__module__
        name = component_type.__name__
        return module == self.class_module and name == self.class_name


def rebase_to_origin(locator: Locator) -> Locator | None:
    """
    This rebase from Origin.live to Origin.source
    It returns None if the locator is not valid.
    If the locator is already in Origin.source, it returns the locator unchanged.
    """
    if not locator:
        return None
    if locator.origin == Origin.source:
        return locator

    locator = dataclasses.replace(locator, origin=Origin.source)  # change origin to source immediately

    # todo probably this should go to some other file to avoid circular import issues
    from wwwpy.common.designer import code_strings, html_locator
    html = code_strings.html_from(locator.class_module, locator.class_name)
    if html is None:
        return None

    cst_node = html_locator.locate_node(html, locator.path)
    if cst_node is None:
        return locator

    node_path = html_locator.node_path_from_leaf(cst_node)
    result = dataclasses.replace(locator, path=node_path)
    return result
