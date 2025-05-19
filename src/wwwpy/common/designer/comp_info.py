from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from wwwpy.common.designer import code_info
from wwwpy.common.designer.code_strings import html_from_source
from wwwpy.common.designer.html_parser import CstTree, html_to_tree

logger = logging.getLogger(__name__)


@dataclass
class CompInfo:
    class_package: str
    class_name: str
    tag_name: str
    path: Path
    cst_tree: CstTree


def iter_comp_info_folder(folder: Path, package: str) -> Iterator[CompInfo]:
    """Iterate over all components in the folder."""
    for path in folder.glob('*.py'):
        yield from iter_comp_info(path, package)


def iter_comp_info(path: Path, package: str) -> Iterator[CompInfo]:
    source_code = path.read_text()
    ci = code_info.info(source_code)
    return (c for c in (_to_comp_info(source_code, path, cl, package) for cl in ci.classes) if c is not None)


def _to_comp_info(source_code: str, path: Path, cl: code_info.ClassInfo, package: str) -> CompInfo | None:
    class_name = cl.name
    html = html_from_source(source_code, class_name)
    if html is None:
        logger.warning(f'Cannot find html for {class_name} in {path}')
        return None

    cst_tree = html_to_tree(html)

    return CompInfo(package, class_name, cl.tag_name, path, cst_tree)
