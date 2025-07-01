from __future__ import annotations

import logging
from functools import cached_property

from wwwpy.common.collectionlib import ObservableList

logger = logging.getLogger(__name__)

_node_id = 0


class NodeList(ObservableList):
    def __init__(self, *args):
        super().__init__(*args)
        self._parent = None

    def _item_added(self, item, index):
        if isinstance(item, Node):
            item._parent = self
        else:
            logger.warning(f'Expected Node, got {type(item)}')

    def _item_removed(self, item, index):
        if isinstance(item, Node):
            item._parent = None
        else:
            logger.warning(f'Expected Node, got {type(item)}')

    @property
    def children(self) -> list[Node]:
        return self

    def selected_nodes(self) -> set[Node]:
        uf = [n for n in self.children if n.selected]
        s = set(uf)
        for ch in self.children:
            s.update(ch.selected_nodes())
        return s

    def deselect_all(self):

        for ch in self.children:
            ch.selected = False

        for ch in self.children:
            ch.deselect_all()

    def root(self) -> NodeList:
        if self._parent is None:
            return self
        return self._parent.root()


class Node(NodeList):

    def __init__(self):
        super().__init__()
        self._selected = False

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        if value == self._selected:
            return
        if value is True:
            self.root().deselect_all()
        self._selected = value

    def _perform_click(self):
        self.selected = True

    def _perform_toggle(self):
        raise NotImplementedError

    def __repr__(self):
        return f'Node(id={self.node_id})'

    @cached_property
    def node_id(self) -> int:
        global _node_id
        _node_id += 1
        return _node_id

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)


class Tree(NodeList):
    pass
