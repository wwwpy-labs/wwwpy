from textwrap import dedent

import js
import pytest

from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.component import Component
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent, _tool
from wwwpy.remote.designer.ui.locator_event import LocatorEvent

# todo refactor tests (dry)
#  also add test when there is no internal html,

def_base = ElementDefBase('button', 'js.HTMLButtonElement')


class Comp1Fixture:
    comp1: Component

    def __init__(self, dyn_sys_path: DynSysPath):
        dyn_sys_path.write_module2('comp1lib.py', dedent(
            """
        import js
        import wwwpy.remote.component as wpc
        class Comp1(wpc.Component, tag_name='comp-52cee2aa'):
            div1: js.HTMLDivElement = wpc.element()
            def init_component(self):
                self.element.innerHTML = '''<div data-name="div1">hello</div>'''
        """
        ))
        from comp1lib import Comp1  # noqa, import of dynamic component
        comp1: Component = Comp1()
        js.document.body.appendChild(comp1.element)
        self.comp1 = comp1
        self.target = AddElementIntent('add-label', element_def=def_base)
        self.add_calls = []
        self.target.add_element = lambda *args: self.add_calls.append(args)
        self.locator_event = LocatorEvent.from_element(comp1.div1)

    @property
    def xy(self):
        return element_xy_center(self.comp1.element)


@pytest.fixture
def comp1_fixture(dyn_sys_path: DynSysPath) -> Comp1Fixture:
    return Comp1Fixture(dyn_sys_path)


@pytest.fixture
def target(comp1_fixture: Comp1Fixture) -> AddElementIntent:
    return comp1_fixture.target


@pytest.fixture
def comp1(comp1_fixture):
    yield comp1_fixture.comp1


@pytest.fixture
def xy(comp1_fixture):
    yield comp1_fixture.xy


async def test_simple_submit(comp1, comp1_fixture):
    # GIVEN
    _tool.show()

    # WHEN
    result = comp1_fixture.target.on_submit(comp1_fixture.locator_event)

    # THEN
    assert result is True
    assert len(comp1_fixture.add_calls) == 1
    assert _tool.visible is False


async def test_simple_hover(comp1, comp1_fixture):
    _tool.transition = False

    # WHEN
    comp1_fixture.target.on_hover(comp1_fixture.locator_event)

    # THEN
    assert _tool.visible is True

# todo test
#  hover, should move the SelectionIndicatorFloater to the target
#  click on 'designer' element, should not select the target and keep the selected_intent (maybe this goes in intent_manager_test.py)
