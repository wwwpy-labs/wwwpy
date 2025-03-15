from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import libcst as cst

from wwwpy.common.designer import code_info, html_parser, html_locator
from wwwpy.common.designer.code_info import Attribute
from wwwpy.common.designer.code_strings import html_string_edit
from wwwpy.common.designer.element_library import ElementDef
from wwwpy.common.designer.html_edit import Position, html_add_indexed
from wwwpy.common.designer.html_locator import NodePath, IndexPath

logger = logging.getLogger(__name__)


def add_class_attribute(source_code: str, class_name: str, attr_info: Attribute) -> str:
    source_code_imp = ensure_imports(source_code)
    module = cst.parse_module(source_code_imp)
    transformer = _AddFieldToClassTransformer(class_name, attr_info)
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
    import tempfile
    import shutil

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


def add_component(source_code: str, class_name: str, comp_def: ElementDef, index_path: IndexPath,
                  position: Position) -> AddResult | AddFailed:
    source_code_orig = source_code
    try:
        source_code = ensure_imports(source_code)
        class_info = code_info.class_info(source_code, class_name)
        if class_info is None:
            print(f'Class {class_name} not found inside source ```{source_code}```')
            return None

        attr_name = class_info.next_attribute_name(comp_def.tag_name)
        named_html = comp_def.new_html(attr_name)

        source1 = add_class_attribute(source_code, class_name,
                                      Attribute(attr_name, comp_def.python_type, 'wpc.element()'))

        def manipulate_html(html):
            add = html_add_indexed(html, named_html, index_path, position)
            return add

        source2 = html_string_edit(source1, class_name, manipulate_html)
        new_tree = html_parser.html_to_tree(source2)
        displacement = 0 if position == Position.beforebegin else 1
        indexes = index_path[0:-1] + [index_path[-1] + displacement]
        new_node_path = html_locator.tree_to_path(new_tree, indexes)
        result = AddResult(source2, new_node_path)
    except Exception as e:
        import traceback
        from wwwpy.common.rpc import serialization
        logger.error(f'Error adding component: {e}')
        logger.exception('Full exception report')

        exception_report = AddComponentExceptionReport(traceback.format_exc(), source_code_orig, class_name,
                                                       comp_def.tag_name, index_path, position)
        exception_report_str = serialization.to_json(exception_report, AddComponentExceptionReport)
        logger.error(f'Exception report str:\n{"=" * 20}\n{exception_report_str}\n{"=" * 20}')
        from wwwpy.common.files import str_gzip_base64
        exception_report_b64 = str_gzip_base64(exception_report_str)
        logger.error(f'Exception report b64:\n{"=" * 20}\n{exception_report_b64}\n{"=" * 20}')
        e.exception_report_b64 = exception_report_b64
        return AddFailed(e, exception_report_str, exception_report_b64)
    return result


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


def ensure_imports(source_code: str) -> str:
    required_imports = [
        'import inspect',
        'import logging',
        'import js',
        'import wwwpy.remote.component as wpc',
    ]

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
