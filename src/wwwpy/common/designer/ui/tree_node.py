from __future__ import annotations

from functools import cached_property


class NodeList:

    def __init__(self):
        super().__init__()
        self._selected_nodes = set()

    @cached_property
    def children(self) -> list[Node]:
        return []

    def selected_nodes(self) -> set[Node]:
        s = set({n for n in self.children if n.selected})
        for ch in self.children:
            s.update(ch.selected_nodes())
        return s


class Node(NodeList):

    def __init__(self):
        super().__init__()
        self._selected = False

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        self._selected = value

    def _perform_click(self):
        self._selected = True

    def _perform_toggle(self):
        raise NotImplementedError


class Tree(NodeList):
    pass
