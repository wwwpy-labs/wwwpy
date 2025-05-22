# tree.py
# credits to: https://stackoverflow.com/a/59109706/316766

from pathlib import Path
from typing import Protocol, Iterable

# prefix components:
space = '    '
branch = '│   '
# pointers:
tee = '├── '
last = '└── '


class NodeProtocol(Protocol):
    def iterdir(self) -> Iterable['NodeProtocol']: ...

    def is_dir(self) -> bool: ...

    @property
    def name(self) -> str: ...


def tree(dir_path: NodeProtocol, prefix: str = '', file_size=False):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """
    contents = list(dir_path.iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        fs = '' if not file_size or path.is_dir() else f' ({path.stat().st_size})'
        yield prefix + pointer + path.name + fs
        try:
            if path.is_dir():  # extend the prefix and recurse:
                extension = branch if pointer == tee else space
                # i.e. space because last, └── , above so no more |
                yield from tree(path, prefix=prefix + extension, file_size=file_size)
        except Exception as e:
            yield prefix + f'Error: {e}'


def print_tree(path, printer=print, file_size=True):
    for line in tree(Path(path), file_size=file_size):
        printer(line)


def filesystem_tree_str(path: Path | str) -> str:
    path = Path(path)
    if path.exists():
        tree_str = '\n'.join(tree(path, prefix='    ', file_size=True))
        return f'Filesystem tree for {path}:\n{tree_str}'
    else:
        return f'Filesystem path do not exists `{path}`'


if __name__ == '__main__':
    print_tree(Path(__file__).parent.parent, file_size=True)
