from dataclasses import dataclass
from textwrap import dedent
from typing import List

from wwwpy.common.designer.code_edit import Attribute, add_class_attribute, add_element, add_method, \
    remove_class_attribute, remove_element, ensure_import, AddResult
from wwwpy.common.designer.code_edit import ensure_imports, AddComponentExceptionReport, AddFailed, \
    rename_class_attribute
from wwwpy.common.designer.code_info import info
from wwwpy.common.designer.element_library import element_library, ElementDefBase
from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.html_locator import Node
from wwwpy.common.files import str_ungzip_base64
from wwwpy.common.rpc import serialization


def test_add_class_attribute():
    original_source = """
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
    btn1: HTMLButtonElement = wpc.element()
    """

    # Expected source after adding the new attribute
    expected_source = """
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
    btn1: HTMLButtonElement = wpc.element()
    btn2: HTMLButtonElement = wpc.element()
    """

    modified_source = add_class_attribute(original_source, 'MyElement',
                                          Attribute('btn2', 'HTMLButtonElement', 'wpc.element()'))

    modified_info = info(modified_source)
    expected_info = info(expected_source)

    assert modified_info == expected_info, "The attribute was not added correctly."


def test_add_class_attribute__should_retain_comments_and_style():
    original_source = """
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    """

    expected_source = """
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    btn2: js.HTMLButtonElement = wpc.element()
    """

    modified_source = add_class_attribute(original_source, 'MyElement',
                                          Attribute('btn2', 'js.HTMLButtonElement', 'wpc.element()'))

    assert _remove_import(modified_source) == expected_source


def test_add_class_attribute__should_add_it_on_top_after_other_attributes():
    original_source = """
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    def foo(self):
        pass
    """

    expected_source = """
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    btn2: js.HTMLButtonElement = wpc.element()
    def foo(self):
        pass
    """

    modified_source = add_class_attribute(original_source, 'MyElement',
                                          Attribute('btn2', 'js.HTMLButtonElement', 'wpc.element()'))

    assert _remove_import(modified_source) == expected_source


def test_add_class_attribute__should_honor_classname():
    original_source = """
class MyElement(wpc.Component):
        pass
class MyElement2(wpc.Component):
        pass
    """

    expected_source = """
class MyElement(wpc.Component):
        pass
class MyElement2(wpc.Component):
        btn1: js.HTMLButtonElement = wpc.element()
        pass
    """

    modified_source = add_class_attribute(original_source, 'MyElement2',
                                          Attribute('btn1', 'js.HTMLButtonElement', 'wpc.element()'))

    assert _remove_import(modified_source) == expected_source


# def test_add_class_attribute__non_js_class():
#     ...


def test_remove_class_attribute__should_remove_the_line():
    original_source = """
class MyElement(wpc.Component):
        ele1: HTMLElement = wpc.element()
        ele2: HTMLElement = wpc.element()
    """
    expected_source = """
class MyElement(wpc.Component):
        ele2: HTMLElement = wpc.element()
    """

    modified_source = remove_class_attribute(original_source, 'MyElement', 'ele1')

    assert _remove_import(modified_source) == expected_source


def test_rename_class_attribute():
    original_source = """
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
    btn1: HTMLButtonElement = wpc.element()
    """

    # Expected source after renaming the new attribute
    expected_source = """
import wwwpy.remote.component as wpc

class MyElement(wpc.Component):
    btnSend: HTMLButtonElement = wpc.element()
        """

    modified_source = rename_class_attribute(original_source, 'MyElement', 'btn1', 'btnSend')

    modified_info = info(modified_source)
    expected_info = info(expected_source)

    assert modified_info == expected_info, "The attribute was not renamed correctly."


def test_rename_class_attribute__should_rename_events():
    original_source = """
class MyElement(wpc.Component):
    async def btn1__click(self, event):
        pass
    """

    # Expected source after renaming the new attribute
    expected_source = """
class MyElement(wpc.Component):
    async def btnSend__click(self, event):
        pass
        """

    modified_source = rename_class_attribute(original_source, 'MyElement', 'btn1', 'btnSend')

    modified_info = info(_remove_import(modified_source))
    expected_info = info(expected_source)

    assert modified_info == expected_info, "The event was not renamed correctly."


def test_rename_class_attribute__should_honor_classname():
    original_source = """
class MyElement(wpc.Component):
        btn1: js.HTMLButtonElement = wpc.element()
class MyElement2(wpc.Component):
        btn1: js.HTMLButtonElement = wpc.element()
    """

    expected_source = """
class MyElement(wpc.Component):
        btn1: js.HTMLButtonElement = wpc.element()
class MyElement2(wpc.Component):
        btnSend: js.HTMLButtonElement = wpc.element()
    """

    modified_source = rename_class_attribute(original_source, 'MyElement2', 'btn1', 'btnSend')

    assert _remove_import(modified_source) == expected_source


path01 = [0, 1]


class TestAddElement:
    def test_simple(self):
        original_source = """
class MyElement(wpc.Component):
    def init_component(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div></div>'''
    """

        expected_source = """
class MyElement(wpc.Component):
    btn1: js.Some = wpc.element()
    def init_component(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div><btn data-name="btn1"></btn></div>'''
    """

        edb = ElementDefBase('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, path01, Position.afterend)
        actual = _remove_import(add_result.source_code)

        assert actual == expected_source

    def test_non_js_class(self):
        original_source = dedent("""
    class MyElement(wpc.Component):
        def init_component(self):
            self.element.innerHTML = '''<div></div>'''
        """)

        expected_source = dedent("""
    from remote.comp1 import Comp1
        
    class MyElement(wpc.Component):
        comp1a: Comp1 = wpc.element()
        def init_component(self):
            self.element.innerHTML = '''<div></div><comp-1 data-name="comp1a"></comp-1>'''
        """)

        edb = ElementDefBase('comp-1', 'remote.comp1.Comp1')
        add_result = add_element(original_source, 'MyElement', edb, [0], Position.afterend)
        assert isinstance(add_result, AddResult), f'add_result={add_result}'
        actual = _remove_import(add_result.source_code)

        assert _no_empty_lines(actual) == _no_empty_lines(expected_source)

    def test_gen_html(self):
        original_source = """
class MyElement:
    def init_component(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div></div>'''
    """

        expected_source = """
class MyElement:
    btn1: js.Some = wpc.element()
    def init_component(self):
        self.element.innerHTML = '''<div id='foo'><div></div><div id='target'></div>
<btn data-name="btn1" attr1="bar"></btn></div>'''
    """

        @dataclass
        class MyElementDef(ElementDefBase):
            def new_html(self, data_name: str) -> str:
                return f'\n<btn data-name="{data_name}" attr1="bar"></btn>'

        component_def = MyElementDef('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', component_def, path01, Position.afterend)

        assert _remove_import(add_result.source_code) == expected_source

    def test_add__afterend(self):
        original_source = _mk_comp('''<div id='foo'><div></div><div id='target'></div></div>''')

        edb = ElementDefBase('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, path01, Position.afterend)

        expected_node_path = [Node("div", 0, {'id': 'foo'}), Node('btn', 2, {'data-name': 'btn1'})]
        assert add_result.node_path == expected_node_path

    def test_add__beforebegin(self):
        original_source = _mk_comp('''<div id='foo'><div></div><div id='target'></div></div>''')

        edb = ElementDefBase('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, path01, Position.beforebegin)

        expected_node_path = [Node("div", 0, {'id': 'foo'}), Node('btn', 1, {'data-name': 'btn1'})]
        assert add_result.node_path == expected_node_path

    def test_add__afterbegin(self):
        original_source = _mk_comp('<div><br></div>')

        edb = ElementDefBase('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, [0], Position.afterbegin)
        if not isinstance(add_result, AddResult):
            raise ValueError(f'unexpected type={add_result}')

        expected_node_path = [Node("div", 0, {}), Node('btn', 0, {'data-name': 'btn1'})]
        assert add_result.node_path == expected_node_path

    def test_add__beforeend(self):
        original_source = _mk_comp('<div><br></div>')

        edb = _ElementDefBaseSimple('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, [0], Position.beforeend)
        if not isinstance(add_result, AddResult):
            raise ValueError(f'unexpected type={add_result}')

        expected_node_path = [Node("div", 0, {}), Node('btn', 1, {})]
        assert add_result.html == '''<div><br><btn></btn></div>'''
        assert add_result.node_path == expected_node_path

    def test_add__afterbegin_text_node(self):
        original_source = _mk_comp('<div>foo</div>')

        edb = _ElementDefBaseSimple('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, [0], Position.afterbegin)
        if not isinstance(add_result, AddResult):
            raise ValueError(f'unexpected type={add_result}')

        assert add_result.html == '''<div><btn></btn>foo</div>'''
        expected_node_path = [Node("div", 0, {}), Node('btn', 0, {})]
        assert add_result.node_path == expected_node_path

    def test_add__beforeend_text_node(self):
        original_source = """
class MyElement:
    def init_component(self):
        self.element.innerHTML = '''<div>foo</div>'''
    """

        edb = _ElementDefBaseSimple('btn', 'js.Some')
        add_result = add_element(original_source, 'MyElement', edb, [0], Position.beforeend)
        if not isinstance(add_result, AddResult):
            raise ValueError(f'unexpected type={add_result}')

        assert add_result.html == '''<div>foo<btn></btn></div>'''
        expected_node_path = [Node("div", 0, {}), Node('btn', 0, {})]
        assert add_result.node_path == expected_node_path


class TestRemoveElement:
    def test_html_and_no_python_attribute(self):
        original_source = _mk_comp("<div></div><div id='target'></div>")
        expected_source = _mk_comp('<div></div>')

        result = remove_element(original_source, 'MyElement', [1])

        assert _remove_import(result) == expected_source

    def test_html_with_attr(self):
        original_source = _mk_comp('<div></div><div data-name="btn1"></div>', attrs=['btn1: js.Some = wpc.element()'])
        expected_source = _mk_comp('<div></div>')
        result = remove_element(original_source, 'MyElement', [1])

        assert _remove_import(result) == expected_source


def test_add_method():
    original_source = """
class MyElement1:
    btn1: js.Some = wpc.element()"""

    expected_source = original_source + """
    
    async def button1__click(self, event):
        pass
    """
    modified_source = add_method(original_source, 'MyElement1', 'button1__click', 'event')
    assert _remove_import(modified_source) == expected_source


def test_add_method_custom_code():
    original_source = """
class MyElement1:
    btn1: js.Some = wpc.element()"""

    expected_source = original_source + """
    
    async def button1__click(self, event):
        pass # custom
    """

    modified_source = add_method(original_source, 'MyElement1', 'button1__click', 'event', instructions='pass # custom')

    assert _remove_import(modified_source) == expected_source


_default_imports = ['import inspect', 'import logging', 'import wwwpy.remote.component as wpc', 'import js', ]


class TestEnsureImports:

    def assert_imports_ok(self, source):
        __tracebackhide__ = True

        def _remove_comment_if_present(line) -> str:
            line = line.strip()
            if '#' in line:
                line = line[:line.index('#')]
            return line.strip()

        modified_source = ensure_imports(source)
        modified_set = [_remove_comment_if_present(l) for l in ensure_imports(source).strip().split('\n')]
        # so it's order independent
        assert set(modified_set) == set(_default_imports)
        return modified_source

    def test_ensure_imports(self):
        self.assert_imports_ok('')

    def test_ensure_imports__should_not_duplicate_imports(self):
        self.assert_imports_ok('\n'.join(_default_imports))

    def test_ensure_imports__wpc_already_present(self):
        self.assert_imports_ok(_default_imports[0])

    def test_ensure_imports__js_already_present(self):
        self.assert_imports_ok(_default_imports[1])

    def test_ensure_imports__with_confounders(self):
        original_source = 'import js # noqa'
        modified_source = self.assert_imports_ok(original_source)
        assert original_source in modified_source

    def test_ensure_import__with_future_annotations(self):
        # original_source = '''"""File selection component."""\n\nfrom __future__ import annotations'''
        original_source = """from __future__ import annotations\n"""
        modified_source = ensure_imports(original_source)
        assert modified_source.startswith(original_source)

    def test_ensure_import__with_future_annotations__and_comment(self):
        original_source = '''"""File selection component."""\n\nfrom __future__ import annotations\n'''
        modified_source = ensure_imports(original_source)
        assert modified_source.startswith(original_source)


class TestEnsureImport:
    def test_simple(self):
        actual = ensure_import('', 'mod1.mod2.Class1')
        expected = 'from mod1.mod2 import Class1'
        assert actual == expected

    def test_import_already_present(self):
        actual = ensure_import('from mod1.mod2 import Class1', 'mod1.mod2.Class1')
        expected = 'from mod1.mod2 import Class1'
        assert actual == expected

    def test_import_with_future_annotation(self):
        actual = ensure_import('from __future__ import annotations\nfrom mod1.mod2 import Class1', 'mod1.mod2.Class1')
        expected = 'from __future__ import annotations\nfrom mod1.mod2 import Class1'
        assert actual == expected

    def test_import_with_future_annotation__and_comment(self):
        actual = ensure_import(
            '"""File selection component."""\n\nfrom __future__ import annotations\nfrom mod1.mod2 import Class1',
            'mod1.mod2.Class1')
        expected = '"""File selection component."""\n\nfrom __future__ import annotations\nfrom mod1.mod2 import Class1'
        assert actual == expected


def placeholder_test_error_reporter():
    err = "some-base64-error-report"
    err1 = str_ungzip_base64(err)
    exc = serialization.from_json(err1, AddComponentExceptionReport)
    print(f'exc: {exc}')
    ed = element_library().by_tag_name(exc.tag_name)
    result = add_element(exc.source_code_orig, exc.class_name, ed, exc.index_path, exc.position)
    if isinstance(result, AddFailed):
        raise result.exception


def _remove_import(source: str) -> str:
    lines = source.split('\n')
    return '\n'.join([line for line in lines if not line.startswith('import ')])


def _no_empty_lines(source: str) -> str:
    lines = source.split('\n')
    return '\n'.join([line for line in lines if line.strip() != ''])


class _ElementDefBaseSimple(ElementDefBase):
    def new_html(self, data_name: str) -> str:
        return f"""<{self.tag_name}></{self.tag_name}>"""


class Test_mk_comp:

    def test_mk_comp(self):
        original_source = dedent(f"""
        class MyElement(wpc.Component):
            def init_component(self):
                self.element.innerHTML = '''xyz'''
            """)

        res = _mk_comp('xyz')

        assert res == original_source, f'Expected:\n{original_source}\nGot:\n{res}'

    def test_mk_comp_with_attrs(self):
        attrs = ['attr1', 'attr2']
        original_source = dedent(f"""
        class MyElement(wpc.Component):
            attr1
            attr2
            def init_component(self):
                self.element.innerHTML = '''xyz'''
            """)

        res = _mk_comp('xyz', attrs)

        assert res == original_source, f'Expected:\n{original_source}\nGot:\n{res}'


def _mk_comp(inner_html: str, attrs: List[str] = ()) -> str:
    indent = ' ' * 4
    clazz = 'class MyElement(wpc.Component):'
    def_init = indent + 'def init_component(self):'
    inner_line = indent * 2 + f"""self.element.innerHTML = '''{inner_html}'''"""
    attr_lines = [indent + attr for attr in attrs]
    res = '\n'.join(['', clazz] + attr_lines + [def_init, inner_line, ''])
    return res
