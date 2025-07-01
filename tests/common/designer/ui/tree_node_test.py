from __future__ import annotations

from wwwpy.common.designer.ui.tree_node import Node, NodeList


class TestNode:
    def test_selected(self):
        node = Node()
        assert node.selected is False
        node.selected = True
        assert node.selected is True


class TestNodeList:

    def test_selected_nodes(self):
        # GIVEN
        tree = NodeList()
        node = Node()
        tree.children.append(node)

        # WHEN
        node._perform_click()

        # THEN
        assert node.selected is True
        assert node in tree.selected_nodes()

    def test_selected_nodes_recursive(self):
        # GIVEN
        tree = NodeList()
        node = Node()
        tree.children.append(node)
        sub_node = Node()
        node.children.append(sub_node)

        # WHEN
        sub_node.selected = True

        # THEN
        assert sub_node in tree.selected_nodes()

    def test_only_one_should_be_selected(self):
        # GIVEN
        tree = NodeList()
        node = Node()
        node2 = Node()
        tree.children.append(node)
        tree.children.append(node2)
        sub_node = Node()
        node.children.append(sub_node)

        # WHEN
        sub_node.selected = True
        node2._perform_click()

        # THEN
        assert tree.selected_nodes() == {node2}
