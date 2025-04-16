from __future__ import annotations

import logging
from typing import Callable

import libcst as cst

from wwwpy.common import modlib

logger = logging.getLogger(__name__)


def html_string_edit(source_code: str, class_name: str, html_manipulator: Callable[[str], str]) -> str:
    """This function modifies the HTML string in the source code using the provided manipulator function.
    It only modifies the HTML string within the specified class.
    Supports both triple single-quoted and triple double-quoted strings.
    """
    tree = cst.parse_module(source_code)
    transformer = _HTMLStringUpdater(class_name, html_manipulator)
    modified_tree = tree.visit(transformer)
    return modified_tree.code


def html_from(module: str, class_name: str) -> str | None:
    path = modlib._find_module_path(module)
    if not path:
        return None
    source_code = path.read_text()
    return html_from_source(source_code, class_name)


def html_from_source(source_code: str, class_name: str) -> str | None:
    """This function extracts the HTML string from the source code."""
    logger.debug(f'html_from_source {class_name} source_code=`{source_code}`')

    html_res = []

    def html_manipulator(html):
        html_res.append(html)
        return html

    html_string_edit(source_code, class_name, html_manipulator)  # improper use to capture html
    if not html_res:
        return None
    return html_res[0]


class _HTMLStringUpdater(cst.CSTTransformer):
    def __init__(self, class_name: str, html_manipulator: Callable[[str], str]):
        super().__init__()
        self.class_name = class_name
        self.html_manipulator = html_manipulator
        self.current_class = None

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        self.current_class = node.name.value

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.CSTNode:
        self.current_class = None
        return updated_node

    def leave_SimpleString(self, original_node: cst.SimpleString, updated_node: cst.SimpleString) -> cst.CSTNode:
        if self.current_class == self.class_name:
            if (original_node.value.startswith('"""') and original_node.value.endswith('"""')) or \
                    (original_node.value.startswith("'''") and original_node.value.endswith("'''")):
                quote_type = original_node.value[:3]
                original_html = original_node.value[3:-3]
                modified_html = self.html_manipulator(original_html)
                return updated_node.with_changes(value=f'{quote_type}{modified_html}{quote_type}')
        return updated_node
