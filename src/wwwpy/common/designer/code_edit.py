from __future__ import annotations

import logging
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import libcst as cst

from wwwpy.common.designer import code_info, html_parser, html_locator
from wwwpy.common.designer.code_info import Attribute
from wwwpy.common.designer.code_strings import html_string_edit
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.common.designer.html_edit import Position, html_add_indexed, html_remove_indexed
from wwwpy.common.designer.html_locator import NodePath, IndexPath, data_name

logger = logging.getLogger(__name__)


def add_class_attribute(source_code: str, class_name: str, attr_info: Attribute) -> str:
    source_code_imp = ensure_imports(source_code)
    module = cst.parse_module(source_code_imp)
    transformer = _AddFieldToClassTransformer(class_name, attr_info)
    modified_tree = module.visit(transformer)

    return modified_tree.code


def remove_class_attribute(source_code: str, class_name: str, attr_name: str) -> str:
    source_code_imp = ensure_imports(source_code)
    module = cst.parse_module(source_code_imp)
    transformer = _RemoveFieldFromClassTransformer(class_name, attr_name)
    modified_tree = module.visit(transformer)

    return modified_tree.code


def rename_class_attribute(source_code: str, class_name: str, old_attr_name: str, new_attr_name: str):
    source_code_imp = ensure_imports(source_code)
    # tree1 = tree0.visit(_RenameFieldInClassTransformer(class_name, old_attr_name, new_attr_name))
    tree0 = (cst.parse_module(source_code_imp).
             visit(_RenameMethodEventsInClassTransformer(class_name, old_attr_name, new_attr_name)))
    code_rope = _rope_rename_class_attribute(tree0.code, class_name, old_attr_name, new_attr_name)

    return code_rope


def _rope_rename_class_attribute(source_code: str, class_name: str, old_attr_name: str, new_attr_name: str):
    temp_dir = Path(tempfile.mkdtemp())
    try:
        temp_file = temp_dir / 'temp.py'
        temp_file.write_text(source_code)
        return _rope_rename_class_attribute_in_project(temp_dir, temp_file, class_name, old_attr_name, new_attr_name)
    finally:
        shutil.rmtree(temp_dir)


def _rope_rename_class_attribute_in_project(project_dir: Path, file_path: Path, class_name: str, old_attr_name: str,
                                            new_attr_name: str):
    from rope.base.project import Project
    from rope.base.libutils import path_to_resource
    from rope.refactor.rename import Rename
    import re
    project = Project(str(project_dir))
    resource = path_to_resource(project, str(file_path))
    orig_code = resource.read()
    pattern = rf'class\s+{class_name}\b[\s\S]*?\b{old_attr_name}\b'
    match = re.search(pattern, orig_code)
    if not match:
        return orig_code
    name_offset = match.start() + match.group(0).rfind(old_attr_name)
    rename = Rename(project, resource, name_offset)
    changes = rename.get_changes(new_attr_name)
    project.do(changes)
    project.close()
    return resource.read()


@dataclass
class AddResult:
    source_code: str
    node_path: NodePath
    html: str


@dataclass
class AddFailed:
    exception: Exception
    exception_report_str: str
    exception_report_b64: str


@dataclass
class AddComponentExceptionReport:
    stack_trace: str
    source_code_orig: str
    class_name: str
    tag_name: str
    index_path: IndexPath
    position: Position


def add_element(source_code: str, class_name: str, edb: ElementDefBase, index_path: IndexPath,
                position: Position) -> AddResult | AddFailed:
    source_code_orig = source_code
    try:
        imp_tuple = _required_imports_default
        type_import, type_name = _decode_type(edb.python_type)
        if type_import:
            imp_add = f'from {type_import} import {type_name}'
            imp_tuple = (imp_tuple + (imp_add,))

        source_code = ensure_imports(source_code, imp_tuple)
        class_info = code_info.class_info(source_code, class_name)
        if class_info is None:
            print(f'Class {class_name} not found inside source ```{source_code}```')
            return None

        attr_name = class_info.next_attribute_name(edb.tag_name)
        named_html = edb.new_html(attr_name)

        source1 = add_class_attribute(source_code, class_name,
                                      Attribute(attr_name, type_name, 'wpc.element()'))
        changed_html = []

        def manipulate_html(html):
            add = html_add_indexed(html, named_html, index_path, position)
            changed_html.append(add)
            return add

        source2 = html_string_edit(source1, class_name, manipulate_html)
        new_tree = html_parser.html_to_tree(source2)
        if position == Position.afterbegin:
            indexes = index_path + [0]
        elif position == Position.beforeend:
            indexes = index_path + [-1]
        else:
            displacement = 0 if position == Position.beforebegin else 1
            indexes = index_path[0:-1] + [index_path[-1] + displacement]
        new_node_path = html_locator.tree_to_path(new_tree, indexes)
        result = AddResult(source2, new_node_path, changed_html[0])
    except Exception as e:
        import traceback
        from wwwpy.common.rpc import serialization
        logger.error(f'Error adding component: {e}')
        logger.exception('Full exception report')

        exception_report = AddComponentExceptionReport(traceback.format_exc(), source_code_orig, class_name,
                                                       edb.tag_name, index_path, position)
        exception_report_str = serialization.to_json(exception_report, AddComponentExceptionReport)
        logger.error(f'Exception report str:\n{"=" * 20}\n{exception_report_str}\n{"=" * 20}')
        from wwwpy.common.files import str_gzip_base64
        exception_report_b64 = str_gzip_base64(exception_report_str)
        logger.error(f'Exception report b64:\n{"=" * 20}\n{exception_report_b64}\n{"=" * 20}')
        e.exception_report_b64 = exception_report_b64
        return AddFailed(e, exception_report_str, exception_report_b64)
    return result


def _decode_type(type_str: str) -> tuple[str, str]:
    """
    Given a type string like 'wwwpy.remote.component.Component', return the import path and the class name.
    """
    if type_str.startswith('js.'):
        return '', type_str
    if '.' in type_str:
        parts = type_str.rsplit('.', 1)
        return '.'.join(parts[:-1]), parts[-1]
    return '', type_str


class _RenameFieldInClassTransformer(cst.CSTTransformer):
    def __init__(self, class_name, old_field_name, new_field_name):
        super().__init__()
        self.class_name = class_name
        self.old_field_name = old_field_name
        self.new_field_name = new_field_name

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value != self.class_name:
            return original_node
        new_body = []
        for item in updated_node.body.body:
            if isinstance(item, cst.SimpleStatementLine) and isinstance(item.body[0], cst.AnnAssign):
                ann_assign = item.body[0]
                if ann_assign.target.value == self.old_field_name:
                    new_body.append(
                        item.with_changes(body=[ann_assign.with_changes(target=cst.Name(self.new_field_name))]))
                else:
                    new_body.append(item)
            else:
                new_body.append(item)
        return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))


# class _RenameMethodEventsInClassTransformer(cst.CSTTransformer):
#     """This transformer given an old_file_name='btn1' and new_field_name='btn2' will rename all the methods that
#      starts with 'btn1__' to 'btn2__'"""
#     def __init__(self, class_name, old_field_name, new_field_name):
#         super().__init__()

class _RenameMethodEventsInClassTransformer(cst.CSTTransformer):
    def __init__(self, class_name, old_field_name, new_field_name):
        super().__init__()
        self.class_name = class_name
        self.old_field_name = old_field_name
        self.new_field_name = new_field_name

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value != self.class_name:
            return original_node
        new_body = []
        for item in updated_node.body.body:
            if isinstance(item, cst.FunctionDef):
                if item.name.value.startswith(self.old_field_name + '__'):
                    new_body.append(item.with_changes(
                        name=cst.Name(item.name.value.replace(self.old_field_name, self.new_field_name))))
                else:
                    new_body.append(item)
            else:
                new_body.append(item)
        return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))


class _AddFieldToClassTransformer(cst.CSTTransformer):
    def __init__(self, class_name, new_field: Attribute):
        super().__init__()
        self.class_name = class_name
        self.new_field = new_field

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value != self.class_name:
            return original_node
        # Check if the type is a composite name (contains a dot)
        if '.' in self.new_field.type:
            base_name, attr_name = self.new_field.type.rsplit('.', 1)
            annotation = cst.Annotation(cst.Attribute(value=cst.Name(base_name), attr=cst.Name(attr_name)))
        else:
            annotation = cst.Annotation(cst.Name(self.new_field.type))

        new_field_node = cst.SimpleStatementLine([
            cst.AnnAssign(
                target=cst.Name(self.new_field.name),
                annotation=annotation,
                value=None if self.new_field.default is None else cst.parse_expression(self.new_field.default)
            )
        ])

        # Find the position to insert the new attribute
        last_assign_index = 0
        for i, item in enumerate(updated_node.body.body):
            if isinstance(item, cst.SimpleStatementLine) and isinstance(item.body[0], cst.AnnAssign):
                last_assign_index = i + 1

        new_body = list(updated_node.body.body)
        new_body.insert(last_assign_index, new_field_node)

        return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))


class _RemoveFieldFromClassTransformer(cst.CSTTransformer):
    def __init__(self, class_name, field_name):
        super().__init__()
        self.class_name = class_name
        self.field_name = field_name

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value != self.class_name:
            return original_node

        new_body = []
        for item in updated_node.body.body:
            # Check if this is an annotated assignment with the target field name
            if (isinstance(item, cst.SimpleStatementLine) and
                    isinstance(item.body[0], cst.AnnAssign) and
                    isinstance(item.body[0].target, cst.Name) and
                    item.body[0].target.value == self.field_name):
                # Skip this item to remove it
                continue
            else:
                new_body.append(item)

        return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))


def add_method(source_code: str, class_name: str, method_name: str, method_args: str,
               instructions: str = 'pass') -> str:
    source_code_imp = ensure_imports(source_code)
    module = cst.parse_module(source_code_imp)
    transformer = _AddMethodToClassTransformer(True, class_name, method_name, 'self, ' + method_args, instructions)
    modified_tree = module.visit(transformer)
    return modified_tree.code


class _AddMethodToClassTransformer(cst.CSTTransformer):
    def __init__(self, async_def: bool, class_name: str, method_name: str, method_args: str, instructions: str):
        super().__init__()
        self.async_def = async_def
        self.class_name = class_name
        self.method_name = method_name
        self.method_args = method_args
        self.instructions = instructions

    def leave_ClassDef(self, original_node, updated_node):
        if original_node.name.value != self.class_name:
            return original_node

        parsed_instructions = cst.parse_module(self.instructions).body

        new_method_node = cst.FunctionDef(
            name=cst.Name(self.method_name),
            params=cst.Parameters(
                params=[cst.Param(name=cst.Name(arg.strip())) for arg in self.method_args.split(',') if arg.strip()]
            ),
            body=cst.IndentedBlock(body=parsed_instructions),
            asynchronous=cst.Asynchronous() if self.async_def else None
        )

        new_body = list(updated_node.body.body)
        new_body.append(cst.EmptyLine())
        new_body.append(new_method_node)
        new_body.append(cst.EmptyLine())

        return updated_node.with_changes(body=updated_node.body.with_changes(body=new_body))


_required_imports_default = (
    'import inspect',
    'import logging',
    'import js',
    'import wwwpy.remote.component as wpc',
)


def ensure_imports(source_code: str, required_imports: tuple[str, ...] = _required_imports_default) -> str:
    def _remove_comment_if_present(line) -> str:
        line = line.strip()
        if '#' in line:
            line = line[:line.index('#')]
        return line.strip()

    existing_imports = set(_remove_comment_if_present(line) for line in source_code.split('\n')
                           if line.strip().startswith('import'))
    missing_imports = [imp for imp in required_imports if imp not in existing_imports]

    pre, post = _split_on_future_import(source_code)

    result_lines = pre + missing_imports + post
    result_code = '\n'.join(result_lines)
    return result_code


def _split_on_future_import(source_code: str) -> tuple[list[str], list[str]]:
    lines = source_code.split('\n')
    future_index = None
    for i, line in enumerate(lines):
        if line.startswith('from __future__ import'):
            future_index = i
            break

    if future_index is None:
        return [], lines

    pre = lines[:future_index + 1]
    post = lines[future_index + 1:]
    return pre, post


def remove_element(source_code: str, class_name: str, index_path: IndexPath) -> str | None:
    class_info = code_info.class_info(source_code, class_name)
    if class_info is None:
        print(f'Class {class_name} not found inside source ```{source_code}```')
        return None
    old_html_list = []

    def manipulate_html(html):
        old_html_list.append(html)
        add = html_remove_indexed(html, index_path)
        return add

    source2 = html_string_edit(source_code, class_name, manipulate_html)

    old_html = old_html_list[0]
    old_tree = html_parser.html_to_tree(old_html)
    old_path = html_locator.tree_to_path(old_tree, index_path)
    attr_name = data_name(old_path)
    if attr_name:
        source2 = remove_class_attribute(source2, class_name, attr_name)
    return source2


def ensure_import(source: str, full_name: str) -> str:
    """
    Given a fully qualified name like 'mod1.mod2.Class1', return 'from mod1.mod2 import Class1'.
    If the import is already present, return the source unchanged.
    If a 'from __future__ import annotations' is present, preserve it at the top.
    """
    if not full_name or '.' not in full_name:
        return source
    *modules, class_name = full_name.split('.')
    module_path = '.'.join(modules)
    import_stmt = f'from {module_path} import {class_name}'
    # If already present, return source as is
    if import_stmt in source:
        return source
    lines = source.split('\n')
    # Find the last future import
    future_idx = -1
    for idx, line in enumerate(lines):
        if line.strip().startswith('from __future__ import'):
            future_idx = idx
    if future_idx != -1:
        # Insert after the last future import
        return '\n'.join(lines[:future_idx + 1] + [import_stmt] + lines[future_idx + 1:])
    if source.strip() == '':
        return import_stmt
    return import_stmt + '\n' + source
