import logging
from functools import cached_property
from textwrap import dedent

import js
import pytest

from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.component import Component
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent, _tool
from wwwpy.remote.designer.ui.locator_event import LocatorEvent

logger = logging.getLogger(__name__)


# todo refactor tests (dry)
#  also add test when there is no internal html,


class Comp1Fixture:
    comp1: Component

    def __init__(self, dyn_sys_path: DynSysPath):
        self.dyn_sys_path = dyn_sys_path

    @cached_property
    def div1_locator_event(self) -> LocatorEvent:
        return LocatorEvent.from_element(self.comp1.div1)

    @cached_property
    def default_target(self) -> AddElementIntent:
        t = AddElementIntent('add button label', element_def=ElementDefBase('button', 'js.HTMLButtonElement'))
        self._setup_intent(t)
        return t

    @cached_property
    def itself_target(self) -> AddElementIntent:
        metadata = self.comp1.component_metadata
        self_def_base = ElementDefBase(metadata.tag_name, metadata.class_full_name)
        t = AddElementIntent('add comp1', element_def=self_def_base)
        self._setup_intent(t)
        return t

    def _setup_intent(self, t):
        t.add_element = lambda *args: self.add_calls.append(args)
        t._tool.transition = False  # disable transition for tests

    @cached_property
    def comp1(self) -> Component:
        self.dyn_sys_path.write_module2('comp1lib.py', dedent(
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
        return comp1

    @cached_property
    def add_calls(self):
        return []

    @property
    def xy(self):
        return element_xy_center(self.comp1.element)

    def set_target_to_point_itself(self):
        self_def_base = ElementDefBase(self.comp1.component_metadata.tag_name, 'wpc.Component')
        self.target = AddElementIntent('some-label', element_def=self_def_base)


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
    result = comp1_fixture.default_target.on_submit(comp1_fixture.div1_locator_event)

    # THEN
    assert result is True
    assert len(comp1_fixture.add_calls) == 1
    assert _tool.visible is False


async def test_simple_hover(comp1, comp1_fixture):
    # WHEN
    comp1_fixture.default_target.on_hover(comp1_fixture.div1_locator_event)

    # THEN
    assert _tool.visible is True


async def test_recursive_hover__should_be_avoide(comp1, comp1_fixture):
    # WHEN
    comp1_fixture.itself_target.on_hover(comp1_fixture.div1_locator_event)

    # THEN
    assert _tool.visible is False


async def test_recursive_submit__should_be_avoided(comp1, comp1_fixture):
    # WHEN
    result = comp1_fixture.itself_target.on_submit(comp1_fixture.div1_locator_event)

    # THEN
    assert result is False
    assert _tool.visible is False

# todo test
#  hover, should move the SelectionIndicatorFloater to the target
#  click on 'designer' element, should not select the target and keep the selected_intent (maybe this goes in intent_manager_test.py)
