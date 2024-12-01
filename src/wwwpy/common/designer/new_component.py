from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from wwwpy.common import modlib

import logging

logger = logging.getLogger(__name__)


def is_component(path: Path):
    return (path.is_file() and path.suffix == '.py' and
            path.name.startswith('component'))


def next_name_for(current_files: List[str]) -> tuple[int, str]:
    files = set(current_files)
    for i in range(1, sys.maxsize):
        name = f'component{i}.py'
        if name not in files:
            return i, name
    raise ValueError('Really?')


def next_component_path(folder: Path | None = None) -> tuple[int, Path] | None:
    if folder is None:
        folder = modlib._find_package_directory('remote')
        if folder is None:
            logger.error('remote package not found')
            return None
    index, name = next_name_for([d.name for d in folder.iterdir() if is_component(d)])
    file = folder / name
    assert not file.exists()
    return index, file


def main():
    add()


def add(folder: Path | None = None) -> Path | None:
    if folder is None:
        folder = modlib._find_package_directory('remote')
        if folder is None:
            logger.error('remote package not found')
            return None

    index, name = next_name_for([d.name for d in folder.iterdir() if is_component(d)])
    file = folder / name
    assert not file.exists()
    content = f'''import wwwpy.remote.component as wpc
import js

import logging

logger = logging.getLogger(__name__)

class Component{index}(wpc.Component, tag_name='component-{index}'):
    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div>component-{index}</div>"""
'''
    file.write_text(content)
    return file


if __name__ == '__main__':
    main()
