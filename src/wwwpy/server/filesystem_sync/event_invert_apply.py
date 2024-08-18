import dataclasses
import shutil
from pathlib import Path
from typing import List, Dict, Iterable, Union, Optional

from wwwpy.common import tree
from wwwpy.server.filesystem_sync import Event
from dataclasses import dataclass, field


# production code

def events_invert(fs: Path, events: List[Event]) -> List[Event]:
    root = Node('', '', True)

    """This is the root node of the tree that will be used to keep track of the path changes"""

    def _get_or_create_node(path_str: str) -> Node:
        path_node = _get_node_chain(root, path_str)[-1]
        if path_node is None:
            is_dir = (fs / path_str).is_dir()
            path_node = _create_node(root, path_str, is_dir)
        return path_node

    def augment(event: Event) -> Event:
        if event.event_type == 'modified':
            path_node = _get_or_create_node(event.src_path)
            assert path_node is not None
            path = path_node.final_path
            content = _get_content(Path(fs / path))
            aug = dataclasses.replace(event, content=content)
            return aug
        return event

    def is_deleted_entity(rel: Event) -> bool:
        chain = _get_node_chain(root, rel.src_path)
        for node in chain:
            if node is not None and node.to_ignore:
                return True
        return False

    def mark_ignore(path: str):
        node = _get_or_create_node(path)
        node.to_ignore = True

    relative_events = []
    for e in reversed(events):
        rel = e.relative_to(fs)
        if is_deleted_entity(rel):
            continue
        # we are processing the events backwards in time to go from A_n to A_0
        current_path = rel.dest_path  # this is the path in A_i
        if rel.event_type == 'deleted':
            """mark this entity such as we are ignore all preceding events"""
            mark_ignore(current_path)
        elif rel.event_type == 'modified':
            rel = augment(rel)
            mark_ignore(current_path)
        elif e.event_type == 'moved':
            new_path = rel.src_path  # this is the path in A_(i-1)
            final_node = _get_node_chain(root, current_path)[-1]
            if final_node is None:
                # this is the first rename of this path
                _create_node(root, current_path, (fs / current_path).is_dir())

            _move_node(root, current_path, new_path)  # we mutate the tree backwards in time

        relative_events.insert(0, rel)

    return relative_events


def events_apply(fs: Path, events: List[Event]):
    for event in events:
        _event_apply(fs, event)


def _event_apply(fs: Path, event: Event):
    path = fs / event.src_path
    t = event.event_type
    is_dir = event.is_directory
    if t == 'created':
        if is_dir:
            path.mkdir()
        else:
            path.touch()
    elif t == 'deleted':
        if path.exists():  # it could not exist because of events compression
            if is_dir:
                shutil.rmtree(path)  # again because of events compression we could need to remove a whole tree
            else:
                path.unlink()
    elif t == 'moved':
        shutil.move(path, fs / event.dest_path)
    elif t == 'modified':
        c = event.content
        if isinstance(c, str):
            path.write_text(c)
        elif isinstance(c, bytes):
            path.write_bytes(c)
        else:
            raise ValueError(f"Unsupported content type: {type(c)}")


def _get_content(path: Path):
    assert path.exists()
    assert path.is_file()
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return path.read_bytes()


@dataclass
class Node:
    name: str
    """This is the instant name of the node. It is the name of the node in the A_i state"""
    final_path: str
    """This is the final path of the node in the A_n state. It is a relative complete path"""
    is_directory: bool
    to_ignore: bool = False
    children: Dict[str, 'Node'] = field(default_factory=dict)

    # validate in post init
    def __post_init__(self):
        if '//' in self.final_path:
            raise ValueError(f'Invalid path: {self.final_path}')

    def str(self):
        return f'{self.name}'


def _get_node_chain(root: Node, path: str) -> List[Optional[Node]]:
    if path == '/':
        return [root]
    parts = _get_parts(path)
    current = root
    chain = [root]

    for part in parts:
        if current is None or part not in current.children:
            chain.append(None)
            current = None
        else:
            current = current.children[part]
            chain.append(current)

    return chain


def _get_parts(path):
    return path.strip("/").split("/")


def _create_node(root: Node, final_path: str, is_dir: bool) -> Node:
    if final_path == '':
        return root
    parts = _get_parts(final_path)
    current = root

    for i, name in enumerate(parts):
        if name not in current.children:
            sep = '' if i == 0 else '/'
            path = current.final_path + sep + name
            current.children[name] = Node(name, path, is_dir)
        current = current.children[name]

    return current


def _move_node(root: Node, current_path: str, new_path: str):
    """This function moves a node from the current path to the new path.
    if the new path already exists, we will raise an error"""
    print('\nbefore move')
    print_node(root)
    current_node_chain = _get_node_chain(root, current_path)
    new_node_chain = _get_node_chain(root, new_path)

    if new_node_chain[-1] is not None:
        raise ValueError(f'Path already exists: {new_path}')

    current_node = current_node_chain[-1]
    current_node_parent = current_node_chain[-2]
    new_node_parent = new_node_chain[-2]
    new_name = _get_parts(new_path)[-1]

    current_node_parent.children.pop(current_node.name)
    current_node.name = new_name
    new_node_parent.children[new_name] = current_node

    print('after move')
    print_node(root)
    return


@dataclass
class _NodePrint(tree.NodeProtocol):
    node: Node

    def iterdir(self) -> Iterable[tree.NodeProtocol]:
        return [_NodePrint(child) for child in self.node.children.values()]

    def is_dir(self) -> bool:
        return self.node.is_directory

    @property
    def name(self) -> str:
        msg = f' ({self.node.final_path}) is_dir={self.node.is_directory} is_deleted={self.node.to_ignore}'
        return self.node.str().strip('/') + msg


def print_node(node: Node, printer=print):
    for line in tree.tree(_NodePrint(node)):
        printer(line)
