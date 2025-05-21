from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from wwwpy.common.designer.html_parser import html_to_tree, CstNode, CstTree

logger = logging.getLogger(__name__)


@dataclass()
class Node:
    """This is intended to be serializable because it could cross the client/server boundary."""
    tag_name: str
    """The tag name in lowercase."""
    child_index: int
    """This is the index in the list of children of the parent node.
    It is -1 if the node has no parent.
    """
    attributes: Dict[str, Optional[str]]
    """The HTML attributes of the node."""

    def __post_init__(self):
        assert self.tag_name == self.tag_name.lower()


IndexPath = List[int]
NodePath = List[Node]
"""This is the path from the root to a node in the DOM tree."""


def data_name(path: NodePath) -> str | None:
    """The name of the element in the data dictionary."""
    if len(path) == 0:
        return None
    return path[-1].attributes.get('data-name', None)

def path_to_index(path: NodePath) -> IndexPath:
    return [node.child_index for node in path]


def check_node_path(node_path: IndexPath):
    if len(node_path) > 0 and not isinstance(node_path[0], int):
        raise ValueError(f'Invalid node path: {node_path}')


def node_path_serialize(path: NodePath) -> str:
    return json.dumps([node.__dict__ for node in path])


def node_path_deserialize(serialized: str) -> NodePath:
    node_dicts = json.loads(serialized)
    return [Node(**node_dict) for node_dict in node_dicts]


def locate_node(html: str, path: NodePath) -> CstNode | None:
    cst_tree = html_to_tree(html)
    target_node = _locate_node_rec(cst_tree, path)
    logger.debug(f'locate_node {path} -> {target_node} for html=```{html}```')
    return target_node


def _locate_node_rec(nodes: CstTree, path: NodePath, depth: int = 0) -> CstNode | None:
    if depth >= len(path):
        return None

    target_node = path[depth]
    if target_node.child_index < 0 or target_node.child_index >= len(nodes):
        return None
    node = nodes[target_node.child_index]
    if depth == len(path) - 1:
        return node
    return _locate_node_rec(node.children, path, depth + 1)


def locate_node_indexed(html: str, index_path: IndexPath) -> CstNode | None:
    check_node_path(index_path)
    cst_tree = html_to_tree(html)

    def find_node(nodes: CstTree, path: IndexPath, depth: int) -> CstNode | None:
        if depth >= len(path):
            return None

        child_index = path[depth]
        if child_index < 0 or child_index >= len(nodes):
            return None
        node = nodes[child_index]
        if depth == len(path) - 1:
            return node
        return find_node(node.children, path, depth + 1)

    target_node = find_node(cst_tree, index_path, 0)

    return target_node


def locate_span(html: str, path: NodePath) -> Tuple[int, int] | None:
    """This function locates the position of the node specified by the path in the HTML string.
    The position is represented by the start and end indices of the node in the HTML string.
    """

    node = locate_node(html, path)
    return node.span if node else None


def locate_span_indexed(html: str, index_path: IndexPath) -> Tuple[int, int] | None:
    check_node_path(index_path)
    """This function locates the position of the node specified by the path in the HTML string.
    The position is represented by the start and end indices of the node in the HTML string.
    """

    node = locate_node_indexed(html, index_path)
    return node.span if node else None


def tree_to_path(tree: CstTree, index_path: IndexPath) -> NodePath:
    check_node_path(index_path)
    """This function converts a tree of CstNode objects to a NodePath."""

    def _node(index: int, node: CstNode) -> Node:
        return Node(node.tag_name, index, node.attributes)

    result = []
    children = tree
    for index in index_path:
        if index < 0:
            index = len(children) + index
        node = children[index]
        result.append(_node(index, node))
        children = node.children
    return result


def html_to_node_path(html: str, index_path: IndexPath) -> NodePath:
    check_node_path(index_path)
    tree = html_to_tree(html)
    return tree_to_path(tree, index_path)


def rebase_path(source_html: str, live_path: NodePath) -> NodePath:
    source_tree = html_to_tree(source_html)
    cst_node_list = tree_fuzzy_match(source_tree, live_path)
    last_node = cst_node_list[-1]
    result = node_path_from_leaf(last_node)
    return result


def tree_fuzzy_match(tree: CstTree, node_path: NodePath) -> List[CstNode]:
    """This function finds the best CstNode matches in the tree for the given NodePath."""

    def flatten(t: CstTree) -> List[CstNode]:
        result = []
        for node in t:
            result.append(node)
            result.extend(flatten(node.children))
        return result

    nodes = flatten(tree)

    # for all nodes/node_path pair, compute the similarity
    # and store the node with the highest similarity
    matches = []
    for dx in node_path:
        candidates = []
        for sx in nodes:
            similarity = node_similarity(sx, dx)
            candidates.append((similarity, sx))
        candidates.sort(key=lambda pair: pair[0], reverse=True)
        matches.append(candidates)

    # for each node in the node_path, select the best match
    result: NodePath = []
    for match in matches:
        bm = match[0][1]
        result.append(bm)

    return result


def node_similarity(node1: CstNode, node2: CstNode) -> float:
    """This function computes the similarity between two CstNode objects."""
    # assert isinstance(node1, CstNode)
    # assert isinstance(node2, CstNode)
    # import math
    # level_diff = abs(node1.level - node2.level)
    # level_penality = (1.0 - math.log(level_diff + 1)) if level_diff > 0 else 1.0

    if node1.tag_name != node2.tag_name:
        return 0.05
    attr1 = node1.attributes
    attr2 = node2.attributes

    total_keys = set(attr1.keys()) | set(attr2.keys())

    if not total_keys:  # both nodes have no attributes
        return 1.0  # * level_penalty

    common_keys = set(attr1.keys()) & set(attr2.keys())

    def attr_eq(key) -> bool:
        return attr1[key] == attr2[key]

    if 'data-name' in common_keys:
        return 1.0 if attr_eq('data-name') else 0.0

    def attr_sim(key) -> float:
        eq_points = 0.25 if attr_eq(key) else -0.25
        return 0.5 + eq_points

    similarity = sum(attr_sim(key) for key in common_keys) / len(total_keys)
    return similarity


def node_path_from_leaf(last_node: CstNode) -> NodePath:
    """This function constructs a NodePath from a leaf node."""
    result = []

    current = last_node
    while current is not None:
        node = Node(current.tag_name, current.child_index, current.attributes)
        result.insert(0, node)
        current = current.parent
    return result
