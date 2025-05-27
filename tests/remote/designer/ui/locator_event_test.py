from __future__ import annotations

import logging
from textwrap import dedent

import js
import pytest

from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.locator_lib import Origin
from wwwpy.remote import dict_to_js
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.component import Component
from wwwpy.remote.designer.ui.locator_event import LocatorEvent, find_first_user_component

logger = logging.getLogger(__name__)


class Fixture:
    comp1: Component

    def __init__(self, dyn_sys_path: DynSysPath):
        dyn_sys_path.write_module2('comp1lib.py', dedent(
            """
            import js
            import wwwpy.remote.component as wpc
            class Comp1(wpc.Component, tag_name='comp-121625b3'):
                span1: js.HTMLElement = wpc.element()
                def init_component(self):
                    self.element.innerHTML = '''<span data-name="span1">hello</span>'''
            """
        ))
        from comp1lib import Comp1  # noqa, import of dynamic component
        comp1: Component = Comp1()
        js.document.body.appendChild(comp1.element)
        self.comp1 = comp1

    @property
    def xy(self):
        return element_xy_center(self.comp1.element)


@pytest.fixture
def locator_event_fixture(dyn_sys_path: DynSysPath) -> Fixture:
    return Fixture(dyn_sys_path)


@pytest.fixture
def comp1(locator_event_fixture):
    yield locator_event_fixture.comp1


@pytest.fixture
def xy(locator_event_fixture):
    yield locator_event_fixture.xy


async def test_locator_event_from_pointer_event(comp1, xy):
    # GIVEN
    js_event = js.PointerEvent.new('pointerdown', dict_to_js({'clientX': xy[0], 'clientY': xy[1]}))

    # WHEN
    locator_event = LocatorEvent.from_pointer_event(js_event)

    # THEN
    assert locator_event is not None
    assert isinstance(locator_event, LocatorEvent)
    assert locator_event.main_xy == xy
    assert locator_event.main_element == comp1.span1


def test_locator_event_from_element(comp1, xy):
    # GIVEN

    # WHEN
    locator_event = LocatorEvent.from_element(comp1.span1)

    # THEN
    assert locator_event is not None
    assert isinstance(locator_event, LocatorEvent)
    assert locator_event.main_xy == xy
    assert locator_event.main_element == comp1.span1
    assert locator_event.locator.origin == Origin.source


async def test_position(comp1):
    # GIVEN
    el = comp1.span1
    el.style.position = 'absolute'
    el.style.left = f'30px'
    el.style.top = f'40px'
    el.style.width = f'100px'
    el.style.height = f'50px'

    # WHEN
    locator = LocatorEvent.from_element(comp1.span1, (31, 41))
    calls = []

    def callback(w, h, x, y):
        calls.append((w, h, x, y))
        return Position.afterend

    locator.position_resolver = callback

    # THEN
    assert locator is not None
    assert locator.position() == Position.afterend
    assert calls == [(100, 50, 1, 1)]  # the x and y are relative to the top-left corner of the element


def test_locator_on_body__should_select_first_component(comp1):
    el = comp1.span1
    el.style.position = 'absolute'
    el.style.left = f'30px'
    el.style.top = f'40px'
    el.style.width = f'100px'
    el.style.height = f'50px'

    js_event = js.PointerEvent.new('pointerdown', dict_to_js({'clientX': 10, 'clientY': 15}))

    # WHEN
    locator_event = LocatorEvent.from_pointer_event(js_event)

    # THEN
    assert locator_event is not None
    assert isinstance(locator_event, LocatorEvent)
    assert locator_event.main_xy == (10, 15)
    assert locator_event.main_element is not None  # not yet decided what to select


def test_find_first_user_component(comp1):
    # GIVEN
    # comp1 in the body

    # WHEN
    result = find_first_user_component()

    # THEN
    assert result is not None
    assert isinstance(result, Component)
    assert result is comp1
