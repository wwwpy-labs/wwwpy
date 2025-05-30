from __future__ import annotations

from textwrap import dedent

from tests.common import dyn_sys_path
from wwwpy.common.designer.comp_info import iter_comp_info, CompInfo
from wwwpy.common.designer.html_parser import CstTree


def test_simple_component(dyn_sys_path):
    comp1_path, comp_info_list = _get_comp_info_list(dyn_sys_path, '''<div>hello</div>''')
    ci0 = comp_info_list[0]
    assert ci0.class_package == 'pk1'
    assert ci0.class_name == 'Comp1'
    assert ci0.path == comp1_path
    assert ci0.cst_tree is not None
    assert isinstance(ci0.cst_tree, CstTree)
    div = ci0.cst_tree[0]
    assert div.tag_name == 'div'
    assert div.content == 'hello'

    assert ci0.tag_name == 'comp-1'


class TestLocatorRoot:
    def test_locator_root__should_have_2_children(self, dyn_sys_path):
        # GIVEN
        comp1info = _get_comp1_info(dyn_sys_path, '''<div>hello</div><hr>''')

        # WHEN
        target = comp1info.locator_root

        # THEN
        assert len(target.children) == 2

    def test_children_attributes(self, dyn_sys_path):
        # GIVEN
        comp1info = _get_comp1_info(dyn_sys_path, '''<div>hello<br></div><hr>''')

        # WHEN
        target = comp1info.locator_root

        # THEN
        lt0, lt1 = target.children
        assert lt0.locator.tag_name == 'div'
        assert len(lt0.locator.path) == 1
        assert lt0.locator.path[0].child_index == 0
        assert lt0.cst_node.content == 'hello<br>'

        assert lt1.locator.tag_name == 'hr'
        assert len(lt1.locator.path) == 1
        assert lt1.locator.path[0].child_index == 1

        assert len(lt0.children) == 1
        lt00 = lt0.children[0]
        assert lt00.locator.tag_name == 'br'
        assert len(lt00.locator.path) == 2


def _get_comp1_info(dyn_sys_path, html) -> CompInfo:
    path, l = _get_comp_info_list(dyn_sys_path, html)
    return l[0]


def _get_comp_info_list(dyn_sys_path, html):
    comp1_path = dyn_sys_path.write_module2('pk1/comp1.py', dedent(
        f"""
        import wwwpy.common.component as wpc
        class Comp1(wpc.Component, tag_name='comp-1'):
            def init_component(self):
                self.element.innerHTML = '''{html}'''
        """
    ))
    comp1_info_list = list(iter_comp_info(comp1_path, 'pk1'))
    assert len(comp1_info_list) == 1
    assert isinstance(comp1_info_list[0], CompInfo)
    return comp1_path, comp1_info_list
