from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from wwwpy.common.designer.element_library import NamedListMap


def setup_quickstart(directory: Path, quickstart_name: str):
    assert is_empty_project(directory), f'project is not empty: {directory}'
    source = Path(__file__).parent / quickstart_name
    assert source.exists(), f'quickstart not found: {source}'
    shutil.copytree(source, directory, dirs_exist_ok=True)


# def _check_quickstart(directory: Path):
#     if _do_quickstart(directory):
#         print(f'empty directory, creating quickstart in {directory.absolute()}')
#         _setup_quickstart(directory)
#     else:
#         (directory / 'remote').mkdir(exist_ok=True)


# def _do_quickstart(directory):
#     items = list(directory.iterdir())
#     return all(item.name.startswith('.') for item in items)

def _make_hotreload_work(root_path: Path):
    if not is_empty_project(root_path):
        return

    def _write_empty_package(name: str):
        package = root_path / name
        package.mkdir(exist_ok=True)
        (package / '__init__.py').write_text('')

    for p in ['common', 'remote', 'server']:
        _write_empty_package(p)


@dataclass
class Quickstart:
    name: str
    title: str
    description: str
    path: Path


def quickstart_list() -> NamedListMap[Quickstart]:
    source = Path(__file__).parent
    # keep only files that contains a file called 'readme.txt'
    quickstarts = []

    def add(name: str, readme: Path):
        if not readme.exists():
            return
        lines = readme.read_text().splitlines()
        title = lines[0]
        description = '\n'.join(lines[2:])
        quickstart = Quickstart(name, title, description, source / name)
        quickstarts.append(quickstart)

    for d in source.iterdir():
        if d.is_dir() and not d.name.startswith('.'):
            add(d.name, d / 'readme.txt')
    quickstarts = sorted(quickstarts, key=lambda x: x.name)
    return NamedListMap(quickstarts)


def is_empty_project(root_path: Path | str):
    root_path = Path(root_path)
    from wwwpy.common import files

    def blacklisted(item: Path) -> bool:
        return item.name.startswith('.') or item.name in files.directory_blacklist

    def empty(package: str) -> bool:
        directory = root_path / package
        if not directory.exists():
            return True
        init = directory / '__init__.py'

        if init.exists() and init.read_text().strip() != '':
            return False

        def is_init(item: Path) -> bool:
            return item.name == '__init__.py'

        return all(blacklisted(item) or is_init(item) for item in directory.iterdir())

    known = {'common', 'remote', 'server'}
    known_empty = all(empty(folder) for folder in known)
    rest_ok = all(i.name in known or blacklisted(i) for i in root_path.iterdir())
    result = known_empty and rest_ok
    return result
