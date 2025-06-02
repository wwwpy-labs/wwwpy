from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Iterator

from wwwpy.common.designer import code_info
from wwwpy.common.designer.code_strings import html_from_source
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.common.designer.html_locator import node_path_from_leaf
from wwwpy.common.designer.html_parser import CstTree, html_to_tree, CstNode
from wwwpy.common.designer.locator_lib import Locator, Origin

logger = logging.getLogger(__name__)


class LocatorNode:
    # locator: Locator
    # children: list[LocatorNode]
    # cst_node: CstNode
    _cst_children: list[CstNode]

    def __init__(self, parent: CompInfo, cst: CstTree | CstNode):
        self._parent = parent
        if isinstance(cst, CstTree):
            self._cst_children = list(cst)
        elif isinstance(cst, CstNode):
            self._cst_children = list(cst.children)
            ep = node_path_from_leaf(cst)
            self.locator = Locator(self._parent.class_package, self._parent.class_name, ep, Origin.source)
            self.cst_node = cst
        else:
            raise TypeError(f'Expected CstTree or CstNode, got {type(cst)}')

    @cached_property
    def children(self) -> list[LocatorNode]:
        """The children of this node in the CST tree."""
        return [LocatorNode(self._parent, c) for c in self._cst_children]


# class LocatorTree(UserList[LocatorNode]):
#     parent: CompInfo
#     cst_tree: CstTree
#
#     def __init__(self, parent: CompInfo, cst: CstTree):
#         nodes = (LocatorNode())
#         super().__init__()


# todo extend CompInfo such as it provides the means for CompStructure component to show
#  the tree structure of the component's HTML.
#  think about a couple of design patterns to achieve this.
@dataclass
class CompInfo:
    """If the html is not found, no instance of this class is created."""
    class_package: str  # todo rename to class_module
    class_name: str
    tag_name: str
    path: Path
    cst_tree: CstTree

    @cached_property
    def locator_root(self) -> LocatorNode:
        """The CST tree of the component's HTML.
        This is lazy initialized"""
        return LocatorNode(self, self.cst_tree)

    @property
    def class_full_name(self) -> str:
        return f'{self.class_package}.{self.class_name}'


@dataclass
class ComponentDef(ElementDefBase):
    comp_info: CompInfo


def iter_comp_info_folder(folder: Path, package: str) -> Iterator[CompInfo]:
    """Iterate over all components in the folder."""
    logger.debug(f'Iterating over components in {folder}')
    for path in sorted(folder.glob('*.py'), key=lambda p: p.stem):
        yield from iter_comp_info(path, package + '.' + path.stem)


def iter_comp_info(path: Path, package: str) -> Iterator[CompInfo]:
    """Return a generator that yields CompInfo for each Component in the given python file."""
    logger.debug(f'Iterating over components in {path}')
    source_code = path.read_text()
    ci = code_info.info(source_code)
    return (c for c in (_to_comp_info(source_code, path, cl, package) for cl in ci.classes) if c is not None)


def _to_comp_info(source_code: str, path: Path, cl: code_info.ClassInfo, package: str) -> CompInfo | None:
    class_name = cl.name
    html = html_from_source(source_code, class_name)
    if html is None:
        logger.warning(f'Cannot find html for {class_name} in {path}')
        return None

    cst_tree = html_to_tree(html)

    return CompInfo(package, class_name, cl.tag_name, path, cst_tree)
