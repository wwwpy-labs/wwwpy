from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, List, Any

from wwwpy.common.collectionlib import ListMap


@dataclass(frozen=True)
class Help:
    description: str
    url: str


_empty_help = Help("", "")


@dataclass
class NameHelp:
    name: str
    help: Help = field(default=_empty_help)

    @property
    def python_name(self) -> str:
        return self.name.replace('-', '_')


@dataclass
class EventDef(NameHelp):
    """Definition of an event of an HTML element."""
    pass




@dataclass
class AttributeDef(NameHelp):
    """Definition of an attribute of an HTML element."""
    values: list[str] = field(default_factory=list)
    boolean: bool = False
    mandatory: bool = False
    default_value: Optional[str] = None


class NamedListMap(ListMap):
    def __init__(self, args):
        super().__init__(args, key_func=lambda x: x.name)


@dataclass
class ElementDef:
    tag_name: str
    python_type: str
    help: Help = field(default=_empty_help)
    gen_html: Optional[Callable[[ElementDef, str], str]] = None
    """A function that generates the HTML for the element. It takes the data-name of the element as argument."""

    attributes: NamedListMap[AttributeDef] = field(default_factory=list)
    events: NamedListMap[EventDef] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.attributes, ListMap):
            self.attributes = NamedListMap(self.attributes)
        if not isinstance(self.events, ListMap):
            self.events = NamedListMap(self.events)

    def new_html(self, data_name: str) -> str:
        gen_html = self.gen_html or ElementDef.default_gen_html
        return gen_html(self, data_name)

    @classmethod
    def default_gen_html(cls, element_def: ElementDef, data_name: str) -> str:
        return f'\n<{element_def.tag_name} data-name="{data_name}"></{element_def.tag_name}>'


class ElementLibrary:
    def __init__(self):
        self.elements: List[ElementDef] = []

    def by_tag_name(self, tag_name: str) -> Optional[ElementDef]:
        for element in self.elements:
            if element.tag_name == tag_name:
                return element
        return None


_element_library: ElementLibrary = None


def element_library() -> ElementLibrary:
    global _element_library
    if _element_library is None:
        _element_library = ElementLibrary()
        from wwwpy.common.designer.el_shoelace import _shoelace_elements_def
        _element_library.elements.extend(_shoelace_elements_def())
        from .el_standard import _standard_elements_def
        _element_library.elements.extend(_standard_elements_def())
    return _element_library
