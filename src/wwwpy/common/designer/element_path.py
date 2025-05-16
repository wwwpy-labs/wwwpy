from __future__ import annotations

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
class ElementPath:
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
