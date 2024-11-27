"""Module library for finding module paths and roots."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

def _find_module_path(module_name: str) -> Path | None:
    """Finds the path of a module without loading it."""
    parts = module_name.split('.')
    for sys_path in map(Path, sys.path):
        module_path = sys_path.joinpath(*parts)
        py_file = module_path.with_suffix('.py')
        init_file = module_path / '__init__.py'

        if py_file.is_file():
            return py_file
        if module_path.is_dir() and init_file.is_file():
            return init_file

    return None

def _find_package_directory(package_name) -> Path | None:
    """Finds the directory of a package without loading it."""
    path = _find_module_path(package_name)
    if not path:
        return None
    if path.name != '__init__.py':
        raise ValueError(f'package {package_name} is not a package')
    return path.parent


def _find_module_root(fqn, full_path):
    parts = fqn.split('.')
    relative_path = os.path.join(*parts[:-1]) + '.py'
    full_path = os.path.abspath(full_path)
    index = full_path.rfind(relative_path)
    if index == -1:
        return None
    return full_path[index:]
