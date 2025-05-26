from textwrap import dedent

import js

from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.remote.designer.ui.design_aware import LocatorEvent
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent, _tool


async def test_simple_submit(dyn_sys_path: DynSysPath):
    comp1_path = dyn_sys_path.write_module2('comp1.py', dedent(
        """
        import js
        import wwwpy.remote.component as wpc
        class Comp1(wpc.Component, tag_name='comp-52cee2aa'):
            div1: js.HTMLDivElement = wpc.element()
            def init_component(self):
                self.element.innerHTML = '''<div data-name="div1">hello</div>'''
        """
    ))

    # on_exit(injector._clear)
    # canvas_selection = CanvasSelection()
    # injector.bind(canvas_selection)

    from comp1 import Comp1  # noqa, import of dynamic component
    c1 = Comp1()
    js.document.body.appendChild(c1.element)

    def_base = ElementDefBase('button', 'js.HTMLButtonElement')
    target = AddElementIntent('add-label', element_def=def_base)
    add_calls = []
    target.add_element = lambda *args: add_calls.append(args)
    locator_event = LocatorEvent.from_element(c1.div1)
    _tool.show()
    # WHEEN
    result = target.on_submit(locator_event)

    # THEN
    assert result is True
    assert len(add_calls) == 1
    assert _tool.visible is False


async def test_simple_hover(dyn_sys_path: DynSysPath):
    comp1_path = dyn_sys_path.write_module2('comp1.py', dedent(
        """
        import js
        import wwwpy.remote.component as wpc
        class Comp1(wpc.Component, tag_name='comp-52cee2aa'):
            div1: js.HTMLDivElement = wpc.element()
            def init_component(self):
                self.element.innerHTML = '''<div data-name="div1">hello</div>'''
        """
    ))

    from comp1 import Comp1  # noqa, import of dynamic component
    c1 = Comp1()
    js.document.body.appendChild(c1.element)

    def_base = ElementDefBase('button', 'js.HTMLButtonElement')
    target = AddElementIntent('add-label', element_def=def_base)
    add_calls = []
    target.add_element = lambda *args: add_calls.append(args)
    locator_event = LocatorEvent.from_element(c1.div1)
    _tool.transition = False

    # WHEN
    target.on_hover(locator_event)

    # THEN
    assert _tool.visible is True

# todo test
#  hover, should move the SelectionIndicatorFloater to the target
#  click on 'designer' element, should not select the target and keep the selected_intent (maybe this goes in intent_manager_test.py)
