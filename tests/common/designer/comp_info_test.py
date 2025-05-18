from __future__ import annotations

from textwrap import dedent

from tests.common import dyn_sys_path
from wwwpy.common.designer.comp_info import iter_comp_info, CompInfo
from wwwpy.common.designer.html_parser import CstTree


def test_simple_component(dyn_sys_path):
    comp1_path = dyn_sys_path.write_module2('comp1.py', dedent(
        """
        import wwwpy.common.component as wpc
        class Comp1(wpc.Component, tag_name='comp-1'):
            def init_component(self):
                self.element.innerHTML = '''<div>hello</div>'''
        """
    ))

    target = list(iter_comp_info(comp1_path))
    assert len(target) == 1
    assert isinstance(target[0], CompInfo)
    ci0 = target[0]
    assert ci0.class_name == 'Comp1'
    assert ci0.path == comp1_path
    assert ci0.cst_tree is not None
    assert isinstance(ci0.cst_tree, CstTree)
    div = ci0.cst_tree[0]
    assert div.tag_name == 'div'
    assert div.content == 'hello'

    assert ci0.tag_name == 'comp-1'
