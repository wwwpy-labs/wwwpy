from __future__ import annotations

import logging
from dataclasses import dataclass, field
from functools import cached_property

import js
import pytest
from pyodide.ffi import create_proxy

from tests.remote.remote_fixtures import clean_document_now
from tests.remote.rpc4tests_helper import rpctst_exec
from wwwpy.common import injector
from wwwpy.common.injector import register, inject
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.designer.ui.action_manager import ActionManager, Action
from wwwpy.remote.designer.ui.action_manager import HoverEvent, DeselectEvent, TPE, ActionChangedEvent
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.designer.ui.palette import PaletteComponent

logger = logging.getLogger(__name__)


async def test_palette_no_selected_action(action_manager):
    assert action_manager.selected_action is None


async def test_palette_click_action__should_be_selected(action_manager, action1, events):
    await rpctst_exec("page.locator('#action1').click()")

    assert action_manager.selected_action == action1
    assert action1.selected
    assert events.action_changed_events != []


async def test_manual_selection(action_manager, action1, events):
    action_manager.selected_action = action1

    assert action_manager.selected_action == action1
    assert action1.selected
    assert events.action_changed_events != []


async def test_palette_click_twice_action__should_be_deselected(action_manager, action1):
    await rpctst_exec(["page.locator('#action1').click()", "page.locator('#action1').click()"])

    assert action_manager.selected_action is None
    assert not action1.selected


async def test_palette_selecting_different_action__should_deselect_previous(action_manager, action1, action2):
    await rpctst_exec(["page.locator('#action1').click()", "page.locator('#action2').click()"])

    assert action_manager.selected_action == action2
    assert not action1.selected
    assert action2.selected


async def test_palette_should_put_elements_on_screen(action1, action2):
    assert action1.element.isConnected is True
    assert action2.element.isConnected is True


async def test_externally_select_different_action(action_manager, action1, action2):
    # pytest.fail(f'innerHTML: `{js.document.body.innerHTML}`')
    # js.document.body.innerHTML =  '<button id="action1">hello</button>'
    await rpctst_exec("page.locator('#action1').click()")
    action_manager.selected_action = action2

    assert action_manager.selected_action == action2
    assert not action1.selected
    assert action2.selected


class TestUseSelection:
    async def test_selection_and_click__reject_should_not_deselect(self, action_manager, action1, div1, events):
        # GIVEN
        action_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events.accept_events) == 1
        assert action_manager.selected_action is action1

    async def test_selection_and_click__accept_should_deselect(self, action_manager, action1, div1, events):
        # GIVEN
        action_manager.selected_action = action1
        action_manager.on(DeselectEvent).add(lambda ev: ev.accept())

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events.accept_events) == 1
        assert action_manager.selected_action is None


class TestDrag:
    # see Playwright cancel drag here https://github.com/danielwiehl/playwright-bug-reproducer-dnd-cancel/blob/master/tests/reproducer.spec.ts
    # and generally https://chatgpt.com/share/67efcda6-9890-8006-8542-3634aa9249bf

    async def test_selected_drag__accepted_should_deselect(self, action_manager, action1, div1):
        # GIVEN
        action1.accept_execute = True
        action_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None
        assert not action1.selected
        assert action_manager.drag_state == DragFsm.IDLE

    async def test_no_select_start_drag__should_select_palette_action(self, action_manager, action1, div1):
        # GIVEN
        action_manager.selected_action = None

        # WHEN
        await rpctst_exec(["page.locator('#action1').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert action_manager.selected_action is action1
        assert action_manager.drag_state == DragFsm.DRAGGING

    async def test_action1_sel_and_start_drag_on_action2__should_select_action2(self, action_manager, action1, action2,
                                                                                div1):
        # GIVEN
        action_manager.selected_action = action1

        # WHEN
        await rpctst_exec(["page.locator('#action2').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert action_manager.selected_action is action2
        assert action_manager.drag_state == DragFsm.DRAGGING

    async def test_change_selection_with_drag__should_select_action2(self, action_manager, action1, action2, div1):
        # GIVEN
        await rpctst_exec(["page.locator('#action1').click()"])
        x, y = element_xy_center(div1)

        # WHEN
        await rpctst_exec(["page.locator('#action2').hover()", "page.mouse.down()", f"page.mouse.move({x}, {y})"])

        # THEN
        assert action_manager.selected_action is action2
        assert action_manager.drag_state == DragFsm.DRAGGING

    async def test_no_selection_drag_and_drop__accept_should_deselect(self, action_manager, action1, div1, events):
        # GIVEN
        action_manager.selected_action = None
        action_manager.on(DeselectEvent).add(lambda ev: ev.accept())

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None
        assert action_manager.drag_state == DragFsm.IDLE

    async def TODO_test_no_selection_drag_and_drop__should_emit_Drag(self, action_manager, action1, div1, events):
        # GIVEN
        #

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None

        assert len(events.drop_events) == 1, 'one drag event expected'
        assert events.drop_events[0].source_element is action1
        assert events.drop_events[0].target_element is div1

    async def test_no_select_not_enough_drag__should_not_select(self, action_manager, action1):
        # GIVEN
        x, y = element_xy_center(action1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 3}, {y + 3})"])

        # THEN
        assert action_manager.selected_action is None

    async def test_enough_drag__should_select(self, action_manager, action1):
        # GIVEN
        x, y = element_xy_center(action1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 6}, {y + 6})"])

        # THEN
        assert action_manager.selected_action is action1


class TestDragTouch:
    # TODO: implement touch drag tests
    async def todo_action1_click_and_touch_drag_on_action2__should_select_action2(self, action_manager, action1,
                                                                                  action2, div1):
        pass
        # look at `test_action1_click_and_start_drag_on_action2__should_select_action2`
        # look at rpc4tests_test.py how to send touch events


class TestHover:

    async def test_selected_and_hover_on_palette__should_not_emit_Hover(self, action_manager, action1, action2,
                                                                        events):
        # GIVEN
        action_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#action2').hover()")

        # THEN
        assert action_manager.selected_action is action1  # should still be selected
        assert events.hover_events == [], 'hover event emitted'
        assert action2.events == []

    async def test_selected_and_hover_on_div1__should_emit_Hover(self, action_manager, action1, div1, events):
        # GIVEN
        action_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert action_manager.selected_action is action1  # should still be selected

        self._assert_hover_events_arrived_ok(events)

    async def test_drag_and_hover_on_div1__should_emit_Hover(self, action_manager, action1, div1, events):
        # GIVEN
        await rpctst_exec(["page.locator('#action1').hover()", "page.mouse.down()"])
        logger.debug(f'drag state={action_manager.drag_state}')
        # WHEN
        await rpctst_exec(["page.locator('#div1').hover()"])

        # THEN
        self._assert_hover_events_arrived_ok(events)

    def _assert_hover_events_arrived_ok(self, events: EventFixture):
        assert events.hover_events != [], f'hover event not emitted innerHTML: `{js.document.body.innerHTML}`'
        for e in events.hover_events:
            assert e.js_event is not None, 'event should be set'
            assert e.js_event.target is not None, 'target should be set'


class TestStopEvents:
    @pytest.mark.parametrize("event_type", ['click', 'pointerdown', 'pointerup'])
    async def test_stop_event(self, action_manager, action1, event_type, div1):
        # GIVEN
        action_manager.selected_action = action1
        action_manager.on(DeselectEvent).add(lambda ev: ev.accept())

        events = []
        div1.addEventListener(event_type, create_proxy(lambda ev: events.append(ev)))
        logger.debug(f'setup done')
        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert events == [], 'div1 event should not be fired'

    async def test_stop_event_should_not_stop_if_no_selection(self, action_manager, div1):
        # GIVEN
        action_manager.selected_action = None
        events = []
        div1.addEventListener('click', create_proxy(lambda ev: events.append(ev)))

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events) == 1, 'div1 event should be fired'


class TestActionEvents:
    def test_on_selected_programmatically(self, action_manager, action1):
        # WHEN
        action_manager.selected_action = action1

        # THEN
        assert action1.events == ['action1:on_selected']

    async def test_on_select__click(self, action_manager, action1):
        # WHEN
        await rpctst_exec("page.locator('#action1').click()")

        # THEN
        assert action1.events == ['action1:on_selected']

    async def test_on_hover__hover(self, action_manager, action1, div1):
        # WHEN
        action_manager.selected_action = action1
        action1.events.clear()

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert action1.events == ['action1:on_hover']

    async def test_on_execute__drag(self, action_manager, action1, div1):
        # GIVEN
        action1.accept_execute = True

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert action1.events == ['action1:on_selected', 'action1:on_hover', 'action1:on_execute',
                                  'action1:on_deselect']

    async def test_on_execute__click(self, action_manager, action1, div1):
        # GIVEN
        action1.accept_execute = True
        action_manager.selected_action = action1
        action1.events.clear()

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert action1.events == ['action1:on_hover', 'action1:on_execute', 'action1:on_deselect']

    async def test_on_execute__drag_reject(self, action_manager, action1, div1):
        # GIVEN
        action1.accept_execute = False

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert action1.events == ['action1:on_selected', 'action1:on_hover', 'action1:on_execute']

    async def test_on_execute__click_reject(self, action_manager, action1, div1):
        # GIVEN
        action1.accept_execute = False
        action_manager.selected_action = action1
        action1.events.clear()

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert action1.events == ['action1:on_hover', 'action1:on_execute']

    async def test_change_selection_with_drag(self, action1, action2, div1, action_events):
        # GIVEN
        await rpctst_exec(["page.locator('#action1').click()"])
        x, y = element_xy_center(div1)
        action_events.clear()

        # WHEN
        await rpctst_exec(["page.locator('#action2').hover()", "page.mouse.down()", f"page.mouse.move({x}, {y})"])

        # THEN
        assert action_events == ['action1:on_deselect', 'action2:on_selected', 'action2:on_hover', ]


@pytest.fixture
def action_manager(fixture):
    yield fixture.action_manager


@pytest.fixture
def action1(fixture): yield fixture.action1


@pytest.fixture
def action2(fixture): yield fixture.action2


@pytest.fixture
def div1(fixture): yield fixture.div1


@pytest.fixture
def events(fixture): yield fixture.events


@pytest.fixture
def action_events(fixture):
    yield fixture.action_events


class EventFixture:
    def __init__(self):
        self._events = []

    def add(self, event):
        self._events.append(event)

    def filter(self, event_type: type[TPE]) -> list[TPE]:
        return [event for event in self._events if isinstance(event, event_type)]

    @property
    def hover_events(self) -> list[HoverEvent]:
        return self.filter(HoverEvent)

    @property
    def accept_events(self) -> list[DeselectEvent]:
        return self.filter(DeselectEvent)

    @property
    def action_changed_events(self) -> list[ActionChangedEvent]:
        return self.filter(ActionChangedEvent)


@dataclass
class ActionFake(Action):
    action_events: list = None
    events: list = field(default_factory=list)
    accept_execute = False

    def _ev(self, kind):
        e = f'{self.label}:{kind}'
        self.events.append(e)
        self.action_events.append(e)


    def on_selected(self): self._ev('on_selected')

    def on_hover(self, event: HoverEvent): self._ev('on_hover')

    def on_execute(self, event: DeselectEvent):
        self._ev('on_execute')
        if self.accept_execute:
            event.accept()

    def on_deselect(self): self._ev('on_deselect')


@dataclass
class Fixture:
    action_manager: ActionManager = inject()

    @cached_property
    def _palette(self):
        p = PaletteComponent()
        js.document.body.appendChild(p.element)
        return p

    def _add_action(self, label: str) -> ActionFake:
        action = ActionFake(label)
        action.action_events = self.action_events
        palette_item = self._palette.add_action(action)
        palette_item.element.id = label
        action.element = palette_item.element
        return action

    @cached_property
    def action_events(self) -> list:
        return []

    @cached_property
    def action1(self) -> ActionFake:
        return self._add_action('action1')

    @cached_property
    def action2(self) -> ActionFake:
        return self._add_action('action2')

    @cached_property
    def div1(self) -> js.HTMLDivElement:
        div1 = js.document.createElement('div')
        div1.id = 'div1'
        div1.textContent = 'hello'
        js.document.body.appendChild(div1)
        return div1

    @property
    def events(self) -> EventFixture:
        ef = EventFixture()
        self.action_manager._listeners.catch_all.add(lambda e: ef.add(e))
        return ef


@pytest.fixture()
def fixture():
    clean_document_now('begin')
    injector.default_injector.clear()
    am = ActionManager()
    register(am)
    f = Fixture()
    f.action_manager.install()
    try:
        yield f
    finally:
        f.action_manager.uninstall()
        clean_document_now('end')
        injector.default_injector.clear()
