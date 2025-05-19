from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

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
class ElementDefBase:
    tag_name: str
    python_type: str

    def new_html(self, data_name: str) -> str:
        return f"""<{self.tag_name} data-name="{data_name}"></{self.tag_name}>"""


@dataclass
class ElementDef(ElementDefBase):
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
        self._elements: dict[str, ElementDef] = {}

    def _add(self, element: ElementDef) -> None:
        """Add an ElementDef into the internal dict by its tag_name."""
        self._elements[element.tag_name] = element

    @property
    def elements(self) -> tuple[ElementDef, ...]:
        return tuple(list(self._elements.values()))

    def by_tag_name(self, tag_name: str) -> Optional[ElementDef]:
        res = self._elements.get(tag_name, None)
        if res is None:
            from wwwpy.common.designer import el_common
            res = el_common._create_unknown_element_def(tag_name)
            self._add(res)
        return res


_element_library: ElementLibrary = None


def element_library() -> ElementLibrary:
    global _element_library
    if _element_library is None:
        _element_library = ElementLibrary()
        from .el_shoelace import _shoelace_elements_def
        from .el_standard import _standard_elements_def

        for loader in (_shoelace_elements_def, _standard_elements_def):
            for el in loader():
                _element_library._add(el)
    return _element_library
