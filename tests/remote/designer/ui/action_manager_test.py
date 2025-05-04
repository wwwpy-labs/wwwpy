from __future__ import annotations

import logging
from dataclasses import dataclass

import js
import pytest
from pyodide.ffi import create_proxy

from tests.remote.remote_fixtures import clean_document
from tests.remote.rpc4tests_helper import rpctst_exec
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.designer.ui.action_manager import ActionManager
from wwwpy.remote.designer.ui.action_manager import HoverEvent, DeselectEvent, TPE, ActionChangedEvent
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.designer.ui.palette import Action, PaletteComponent

logger = logging.getLogger(__name__)


async def test_palette_no_selected_action(pointer_manager):
    assert pointer_manager.selected_action is None


async def test_palette_click_action__should_be_selected(pointer_manager, action1, events):
    await rpctst_exec("page.locator('#action1').click()")

    assert pointer_manager.selected_action == action1
    assert action1.selected
    assert events.action_changed_events != []


async def test_manual_selection(pointer_manager, action1, events):
    pointer_manager.selected_action = action1

    assert pointer_manager.selected_action == action1
    assert action1.selected
    assert events.action_changed_events != []


async def test_palette_click_twice_action__should_be_deselected(pointer_manager, action1):
    await rpctst_exec(["page.locator('#action1').click()", "page.locator('#action1').click()"])

    assert pointer_manager.selected_action is None
    assert not action1.selected


async def test_palette_selecting_different_action__should_deselect_previous(pointer_manager, action1, action2):
    await rpctst_exec(["page.locator('#action1').click()", "page.locator('#action2').click()"])

    assert pointer_manager.selected_action == action2
    assert not action1.selected
    assert action2.selected


async def test_palette_should_put_elements_on_screen(action1, action2):
    assert action1.element.isConnected is True
    assert action2.element.isConnected is True


async def test_externally_select_different_action(pointer_manager, action1, action2):
    # pytest.fail(f'innerHTML: `{js.document.body.innerHTML}`')
    # js.document.body.innerHTML =  '<button id="action1">hello</button>'
    await rpctst_exec("page.locator('#action1').click()")
    pointer_manager.selected_action = action2

    assert pointer_manager.selected_action == action2
    assert not action1.selected
    assert action2.selected


class TestUseSelection:
    async def test_selection_and_click__reject_should_not_deselect(self, pointer_manager, action1, div1, events):
        # GIVEN
        pointer_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events.accept_events) == 1
        assert pointer_manager.selected_action is action1

    async def test_selection_and_click__accept_should_deselect(self, pointer_manager, action1, div1, events):
        # GIVEN
        pointer_manager.selected_action = action1
        pointer_manager.on(DeselectEvent).add(lambda ev: ev.accept())

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events.accept_events) == 1
        assert pointer_manager.selected_action is None


class TestDrag:
    # see Playwright cancel drag here https://github.com/danielwiehl/playwright-bug-reproducer-dnd-cancel/blob/master/tests/reproducer.spec.ts
    # and generally https://chatgpt.com/share/67efcda6-9890-8006-8542-3634aa9249bf

    async def test_selected_drag__accepted_should_deselect(self, pointer_manager, action1, div1):
        # GIVEN
        pointer_manager.selected_action = action1
        pointer_manager.on(DeselectEvent).add(lambda event: event.accept())

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert pointer_manager.selected_action is None
        assert not action1.selected
        assert pointer_manager.drag_state == DragFsm.IDLE

    async def test_no_select_start_drag__should_select_palette_action(self, pointer_manager, action1, div1):
        # GIVEN
        pointer_manager.selected_action = None

        # WHEN
        await rpctst_exec(["page.locator('#action1').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert pointer_manager.selected_action is action1
        assert pointer_manager.drag_state == DragFsm.DRAGGING

    async def test_action1_sel_and_start_drag_on_action2__should_select_action2(self, pointer_manager, action1, action2,
                                                                                div1):
        # GIVEN
        pointer_manager.selected_action = action1

        # WHEN
        await rpctst_exec(["page.locator('#action2').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert pointer_manager.selected_action is action2
        assert pointer_manager.drag_state == DragFsm.DRAGGING

    async def test_action1_click_and_start_drag_on_action2__should_select_action2(self, pointer_manager, action1,
                                                                                  action2, div1):
        # GIVEN
        await rpctst_exec(["page.locator('#action1').click()"])
        x, y = element_xy_center(div1)

        # WHEN
        await rpctst_exec(["page.locator('#action2').hover()", "page.mouse.down()", f"page.mouse.move({x}, {y})"])

        # THEN
        assert pointer_manager.selected_action is action2
        assert pointer_manager.drag_state == DragFsm.DRAGGING

    async def test_no_selection_drag_and_drop__accept_should_deselect(self, pointer_manager, action1, div1, events):
        # GIVEN
        pointer_manager.selected_action = None
        pointer_manager.on(DeselectEvent).add(lambda ev: ev.accept())

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert pointer_manager.selected_action is None
        assert pointer_manager.drag_state == DragFsm.IDLE

    async def TODO_test_no_selection_drag_and_drop__should_emit_Drag(self, pointer_manager, action1, div1, events):
        # GIVEN
        #

        # WHEN
        await rpctst_exec("page.locator('#action1').drag_to(page.locator('#div1'))")

        # THEN
        assert pointer_manager.selected_action is None

        assert len(events.drop_events) == 1, 'one drag event expected'
        assert events.drop_events[0].source_element is action1
        assert events.drop_events[0].target_element is div1

    async def test_no_select_not_enough_drag__should_not_select(self, pointer_manager, action1):
        # GIVEN
        x, y = element_xy_center(action1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 3}, {y + 3})"])

        # THEN
        assert pointer_manager.selected_action is None

    async def test_enough_drag__should_select(self, pointer_manager, action1):
        # GIVEN
        x, y = element_xy_center(action1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 6}, {y + 6})"])

        # THEN
        assert pointer_manager.selected_action is action1


class TestDragTouch:
    # TODO: implement touch drag tests
    async def todo_action1_click_and_touch_drag_on_action2__should_select_action2(self, pointer_manager, action1,
                                                                                  action2, div1):
        pass
        # look at `test_action1_click_and_start_drag_on_action2__should_select_action2`
        # look at rpc4tests_test.py how to send touch events


class TestHover:

    async def test_selected_and_hover_on_palette__should_not_emit_Hover(self, pointer_manager, action1, action2,
                                                                        events):
        # GIVEN
        pointer_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#action2').hover()")

        # THEN
        assert pointer_manager.selected_action is action1  # should still be selected
        assert events.hover_events == [], 'hover event emitted'

    async def test_selected_and_hover_on_div1__should_emit_Hover(self, pointer_manager, action1, div1, events):
        # GIVEN
        pointer_manager.selected_action = action1

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert pointer_manager.selected_action is action1  # should still be selected

        self._assert_hover_events_arrived_ok(events)

    async def test_drag_and_hover_on_div1__should_emit_Hover(self, pointer_manager, action1, div1, events):
        # GIVEN
        await rpctst_exec(["page.locator('#action1').hover()", "page.mouse.down()"])
        logger.debug(f'drag state={pointer_manager.drag_state}')
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
    async def test_stop_event(self, pointer_manager, action1, event_type, div1):
        # GIVEN
        pointer_manager.selected_action = action1
        pointer_manager.on(DeselectEvent).add(lambda ev: ev.accept())

        events = []
        div1.addEventListener(event_type, create_proxy(lambda ev: events.append(ev)))
        logger.debug(f'setup done')
        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert events == [], 'div1 event should not be fired'

    async def test_stop_event_should_not_stop_if_no_selection(self, pointer_manager, div1):
        # GIVEN
        pointer_manager.selected_action = None
        events = []
        div1.addEventListener('click', create_proxy(lambda ev: events.append(ev)))

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events) == 1, 'div1 event should be fired'


@pytest.fixture
def pointer_manager(fixture):
    yield fixture.pointer_manager


@pytest.fixture
def action1(fixture): yield fixture.action1


@pytest.fixture
def action2(fixture): yield fixture.action2


@pytest.fixture
def div1(fixture): yield fixture.div1


@pytest.fixture
def events(fixture): yield fixture.events


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
class Fixture:
    pointer_manager: ActionManager[Action] = None
    _palette: PaletteComponent = None
    _events: EventFixture = None
    _action1: Action = None
    _action2: Action = None
    _div1: js.HTMLDivElement = None

    def __post_init__(self):
        self._palette = PaletteComponent()
        am = self._palette.action_manager
        self.pointer_manager = am

        # def ie(event: IdentifyEvent):
        #     if event.js_event is None:
        #         raise ValueError('js_event is not set')
        #     target = get_deepest_element(event.js_event.clientX, event.js_event.clientY)
        #     if target.id.startswith('action'):
        #         event.set_action(target._action_fake)
        #
        # am.on(IdentifyEvent).add(ie)

    def _add_action(self, label: str) -> Action:
        action = Action(label)
        palette_item = self._palette.add_action(action)
        palette_item.element.id = label
        action.element = palette_item.element
        # action.element.id = label
        # action.element._action_fake = action
        # action.element.innerText = f'{label}-txt'
        js.document.body.appendChild(palette_item.element)
        return action

    @property
    def action1(self) -> Action:
        if self._action1 is None:
            self._action1 = self._add_action('action1')
        return self._action1

    @property
    def action2(self) -> Action:
        if self._action2 is None:
            self._action2 = self._add_action('action2')
        return self._action2

    @property
    def div1(self) -> js.HTMLDivElement:
        if self._div1 is None:
            self._div1 = js.document.createElement('div')
            self._div1.id = 'div1'
            self._div1.textContent = 'hello'
            js.document.body.appendChild(self._div1)
        return self._div1

    @property
    def events(self) -> EventFixture:
        if self._events is None:
            self._events = EventFixture()
            self.pointer_manager.on_events = self._events.add
        return self._events


@pytest.fixture()
def fixture(clean_document):
    f = Fixture()
    f.pointer_manager.install()
    try:
        yield f
    finally:
        f.pointer_manager.uninstall()
