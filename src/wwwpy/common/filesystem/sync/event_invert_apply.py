import dataclasses
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Iterable, Optional

from wwwpy.common import tree
from wwwpy.common.filesystem.sync import Event

logger = logging.getLogger(__name__)


def events_invert(fs: Path, events: List[Event]) -> List[Event]:
    root = Node('.', '.', True)

    """This is the root node of the tree that will be used to keep track of the path changes"""

    def _get_or_create_node(path_str: str) -> Node:
        path_node = _get_node_chain(root, path_str)[-1]
        if path_node is None:
            is_dir = (fs / path_str).is_dir()
            path_node = _create_node(root, path_str, is_dir)
        return path_node

    def get_final_path(event: Event) -> Path:
        path_node = _get_or_create_node(event.src_path)
        assert path_node is not None
        return Path(fs / path_node.final_path)

    def augment(event: Event) -> Event:
        fp = get_final_path(event)
        content = _get_content(fp)
        if content is None:
            logger.warning(f'Content is None for {fp}')
        aug = dataclasses.replace(event, content=content)
        return aug

    def is_deleted_entity(rel: Event) -> bool:
        chain = _get_node_chain(root, rel.src_path)
        for node in chain:
            if node is not None and node.is_deleted:
                return True
        return False

    def is_modified_entity(rel: Event) -> bool:
        node = _get_node_chain(root, rel.src_path)[-1]
        if node is not None and node.is_modified:
            return True
        return False

    relative_events = []
    for e in reversed(events):
        if e.event_type == 'closed':
            continue
        rel = e.relative_to(fs)
        if rel.src_path == '' or rel.src_path == '.':
            continue  # skip any event on the root
        if is_deleted_entity(rel):
            continue
        # we are processing the events backwards in time to go from A_n to A_0
        if e.event_type == 'moved':
            current_path = rel.dest_path  # this is the path in A_i
            new_path = rel.src_path  # this is the path in A_(i-1)
            final_node = _get_node_chain(root, current_path)[-1]
            if final_node is None:
                # this is the first rename of this path
                _create_node(root, current_path, (fs / current_path).is_dir())

            _move_node(root, current_path, new_path)  # we mutate the tree backwards in time

        if is_modified_entity(rel):
            continue
        if rel.event_type == 'deleted':
            # mark this entity such as we are ignore all preceding events, 'moved' included
            _get_or_create_node(rel.src_path).is_deleted = True
        elif rel.event_type == 'modified':
            if get_final_path(rel).is_dir():
                continue
            rel = augment(rel)
            # mark this entity such as we are ignore all preceding events, except 'moved'
            _get_or_create_node(rel.src_path).is_modified = True

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
            path.mkdir(exist_ok=True)  # todo this is because of dev_mode on rpc signature change
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
        func = None
        if isinstance(c, str):
            func = path.write_text
        elif isinstance(c, bytes):
            func = path.write_bytes
        else:
            raise ValueError(f"Unsupported content type: {type(c)}")

        path.parent.mkdir(parents=True, exist_ok=True)
        func(c)


def _get_content(path: Path):
    assert path.exists(), f'Path does not exist: {path}'
    assert path.is_file(), f'Not a file: {path}'
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
    is_deleted: bool = False
    is_modified: bool = False
    children: Dict[str, 'Node'] = field(default_factory=dict)

    # validate in post init
    def __post_init__(self):
        if '//' in self.final_path:
            raise ValueError(f'Invalid path: {self.final_path}')

    def str(self):
        return f'{self.name}'


def _get_node_chain(root: Node, path: str) -> List[Optional[Node]]:
    if path == '.':
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
            path = current.final_path + '/' + name
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
        msg = f' ({self.node.final_path}) is_dir={self.node.is_directory} is_deleted={self.node.is_deleted}'
        return self.node.str().strip('/') + msg


def print_node(node: Node, printer=print):
    for line in tree.tree(_NodePrint(node)):
        printer(line)


def events_init(source: Path) -> List[Event]:
    result = []
    for path in source.rglob('*'):
        src_path = str(path.relative_to(source))
        if path.is_dir():
            result.append(Event(event_type='created', src_path=src_path, is_directory=True))
        else:
            result.append(Event(event_type='modified', src_path=src_path, is_directory=False,
                                content=_get_content(path)))
    return result
