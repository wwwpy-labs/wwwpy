from __future__ import annotations

import logging
from dataclasses import dataclass, field

import js
import pytest
from pyodide.ffi import create_proxy

from tests.remote.remote_fixtures import clean_document
from tests.remote.rpc4tests_helper import rpctst_exec
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.designer.ui.drag_manager import DragFsm
from wwwpy.remote.designer.ui.pointer_manager import HoverEvent, AcceptEvent, IdentifyEvent, _PE
# todo fix import and rename to PointerManager
from wwwpy.remote.designer.ui.pointer_manager import PointerManager as ActionManager
from wwwpy.remote.jslib import get_deepest_element

logger = logging.getLogger(__name__)


async def test_palette_no_selected_item(action_manager):
    assert action_manager.selected_action is None


# todo rename all item1 to action1 (as well as item2, item3)
async def test_palette_click_item__should_be_selected(palette, action_manager, item1):
    await rpctst_exec("page.locator('#item1').click()")

    assert action_manager.selected_action == item1
    assert item1.selected


async def test_palette_click_item_label__should_be_selected(palette, action_manager, item1):
    await rpctst_exec("page.locator('#item1 > label').click()")

    assert action_manager.selected_action == item1
    assert item1.selected


async def test_manual_selection(action_manager, item1):
    action_manager.selected_action = item1

    assert action_manager.selected_action == item1
    assert item1.selected


async def test_palette_click_twice_item__should_be_deselected(palette, action_manager, item1):
    await rpctst_exec(["page.locator('#item1').click()", "page.locator('#item1').click()"])

    assert action_manager.selected_action is None
    assert not item1.selected


async def test_palette_selecting_different_item__should_deselect_previous(palette, action_manager, item1, item2):
    await rpctst_exec(["page.locator('#item1').click()", "page.locator('#item2').click()"])

    assert action_manager.selected_action == item2
    assert not item1.selected
    assert item2.selected


async def test_palette_should_put_elements_on_screen(palette, item1, item2, item3):
    assert item1.element.isConnected is True
    assert item2.element.isConnected is True
    assert item3.element.isConnected is True


async def test_externally_select_item(palette, action_manager, item1, item2):
    action_manager.selected_action = item1

    assert action_manager.selected_action == item1
    assert item1.selected


async def test_externally_select_different_item(action_manager, item1, item2):
    # pytest.fail(f'innerHTML: `{js.document.body.innerHTML}`')
    # js.document.body.innerHTML =  '<button id="item1">hello</button>'
    await rpctst_exec("page.locator('#item1').click()")
    action_manager.selected_action = item2

    assert action_manager.selected_action == item2
    assert not item1.selected
    assert item2.selected


async def test_externally_deselect_item(palette, item1, item2):
    palette.selected_item = item1
    palette.selected_item = None

    assert palette.selected_item is None
    assert not item1.selected


# class TestPaletteItem:
#
#     def test_selected_should_have_class_selected(self):
#         item = PaletteItemComponent()
#         item.selected = True
#         assert item.element.classList.contains('selected')
#
#     def test_selected_deselected_should_not_have_class_selected(self):
#         item = PaletteItemComponent()
#         item.selected = True
#         item.selected = False
#         assert not item.element.classList.contains('selected')


# class TestFindItemFromElement:
#     def test_find_item_from_element(self, item1):
#         assert find_item_from_element(item1._label) == item1
#
#     def test_find_item_from_element_not_found(self, item1, div1):
#         assert find_item_from_element(div1) is None


class TestUseSelection:
    async def test_selection_and_click__reject_should_not_deselect(self, action_manager, item1, div1, events):
        # GIVEN
        action_manager.selected_action = item1
        action_manager.listeners_for(AcceptEvent).add(lambda ev: None)

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events.accept_events) == 1
        assert action_manager.selected_action is item1

    async def test_selection_and_click__accept_should_deselect(self, action_manager, item1, div1, events):
        # GIVEN
        action_manager.selected_action = item1
        action_manager.listeners_for(AcceptEvent).add(lambda ev: ev.accept())

        # WHEN
        await rpctst_exec("page.locator('#div1').click()")

        # THEN
        assert len(events.accept_events) == 1
        assert action_manager.selected_action is None


class TestDrag:
    # see Playwright cancel drag here https://github.com/danielwiehl/playwright-bug-reproducer-dnd-cancel/blob/master/tests/reproducer.spec.ts
    # and generally https://chatgpt.com/share/67efcda6-9890-8006-8542-3634aa9249bf

    async def test_selected_drag__accepted_should_deselect(self, palette, action_manager, item1, div1):
        # GIVEN
        action_manager.selected_action = item1
        action_manager.listeners_for(AcceptEvent).add(lambda event: event.accept())

        # WHEN
        await rpctst_exec("page.locator('#item1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None
        assert not item1.selected
        assert action_manager.drag_state == DragFsm.IDLE

    async def test_no_select_start_drag__should_select_palette_item(self, action_manager, item1, div1):
        # GIVEN
        action_manager.selected_action = None

        # WHEN
        await rpctst_exec(["page.locator('#item1').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert action_manager.selected_action is item1
        assert action_manager.drag_state == DragFsm.DRAGGING

    async def test_item1_sel_and_start_drag_on_item2__should_select_item2(self, action_manager, item1, item2, div1):
        # GIVEN
        action_manager.selected_action = item1

        # WHEN
        await rpctst_exec(["page.locator('#item2').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

        # THEN
        assert action_manager.selected_action is item2
        assert action_manager.drag_state == DragFsm.DRAGGING

    async def test_item1_click_and_start_drag_on_item2__should_select_item2(self, action_manager, item1, item2, div1):
        # GIVEN
        await rpctst_exec(["page.locator('#item1').click()"])
        x, y = element_xy_center(div1)

        # WHEN
        await rpctst_exec(["page.locator('#item2').hover()", "page.mouse.down()", f"page.mouse.move({x}, {y})"])

        # THEN
        assert action_manager.selected_action is item2
        assert action_manager.drag_state == DragFsm.DRAGGING

    async def test_no_selection_drag_and_drop__accept_should_deselect(self, action_manager, item1, div1, events):
        # GIVEN
        action_manager.selected_action = None
        action_manager.listeners_for(AcceptEvent).add(lambda ev: ev.accept())

        # WHEN
        await rpctst_exec("page.locator('#item1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None
        assert action_manager.drag_state == DragFsm.IDLE

    async def TODO_test_no_selection_drag_and_drop__should_emit_Drag(self, action_manager, item1, div1, events):
        # GIVEN
        #

        # WHEN
        await rpctst_exec("page.locator('#item1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None

        assert len(events.drop_events) == 1, 'one drag event expected'
        assert events.drop_events[0].source_element is item1
        assert events.drop_events[0].target_element is div1

    async def test_no_select_not_enough_drag__should_not_select(self, action_manager, item1):
        # GIVEN
        x, y = element_xy_center(item1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 3}, {y + 3})"])

        # THEN
        assert action_manager.selected_action is None

    async def test_enough_drag__should_select(self, action_manager, item1):
        # GIVEN
        x, y = element_xy_center(item1.element)

        # WHEN
        await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 6}, {y + 6})"])

        # THEN
        assert action_manager.selected_action is item1


class TestDragTouch:
    # TODO: implement touch drag tests
    async def todo_item1_click_and_touch_drag_on_item2__should_select_item2(self, action_manager, item1, item2, div1):
        pass
        # look at `test_item1_click_and_start_drag_on_item2__should_select_item2`
        # look at rpc4tests_test.py how to send touch events


class TestHover:

    async def test_selected_and_hover_on_palette__should_not_emit_Hover(self, action_manager, item1, item2, events):
        # GIVEN
        action_manager.selected_action = item1

        # WHEN
        await rpctst_exec("page.locator('#item2').hover()")

        # THEN
        assert action_manager.selected_action is item1  # should still be selected
        assert events.hover_events == [], 'hover event emitted'

    async def test_selected_and_hover_on_div1__should_emit_Hover(self, action_manager, item1, div1, events):
        # GIVEN
        action_manager.selected_action = item1

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert action_manager.selected_action is item1  # should still be selected

        self._assert_hover_events_arrived_ok(events)

    async def test_drag_and_hover_on_div1__should_emit_Hover(self, action_manager, item1, div1, events):
        # GIVEN
        await rpctst_exec(["page.locator('#item1').hover()", "page.mouse.down()"])
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
    async def test_stop_event(self, action_manager, item1, event_type, div1):
        # GIVEN
        action_manager.selected_action = item1
        action_manager.listeners_for(AcceptEvent).add(lambda ev: ev.accept())

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


@pytest.fixture
def palette(fixture):
    yield fixture.palette


@pytest.fixture
def action_manager(fixture):
    yield fixture.action_manager


@pytest.fixture
def item1(fixture): yield fixture.item1


@pytest.fixture
def item2(fixture): yield fixture.item2


@pytest.fixture
def item3(fixture): yield fixture.item3


@pytest.fixture
def div1(fixture): yield fixture.div1


@pytest.fixture
def events(fixture): yield fixture.events


class EventFixture:
    def __init__(self):
        self._events = []

    def add(self, event):
        self._events.append(event)

    def filter(self, event_type: type[_PE]) -> list[_PE]:
        return [event for event in self._events if isinstance(event, event_type)]

    @property
    def hover_events(self) -> list[HoverEvent]:
        return self.filter(HoverEvent)

    @property
    def accept_events(self) -> list[AcceptEvent]:
        return self.filter(AcceptEvent)


@dataclass()
class ActionItemFake:
    key: str
    name: str
    element: js.HTMLElement = field(default_factory=lambda: js.document.createElement('div'))
    selected: bool = False


@dataclass
class Fixture:
    action_manager: ActionManager = None
    _events: EventFixture = None
    _item1: ActionItemFake = None
    _item2: ActionItemFake = None
    _item3: ActionItemFake = None
    _div1: js.HTMLDivElement = None

    def __post_init__(self):
        am = ActionManager()
        self.action_manager = am

        def ie(event: IdentifyEvent):
            if event.js_event is None:
                raise ValueError('js_event is not set')
            # target = event.js_event.target
            # if target is None:
            #     raise ValueError('target is not set')
            target = get_deepest_element(event.js_event.clientX, event.js_event.clientY)
            if target.id.startswith('item'):
                event.identified_as = 'action'
                event.action = target._item_fake
            elif target.id == 'div1':
                event.identified_as = 'canvas'

        am.listeners_for(IdentifyEvent).add(ie)

    def _add_item(self, label: str) -> ActionItemFake:
        item = ActionItemFake(f'{label}-key', label)
        item.element.id = label
        item.element._item_fake = item
        item.element.innerText = f'{label}-txt'
        js.document.body.appendChild(item.element)
        return item

    @property
    def item1(self) -> ActionItemFake:
        if self._item1 is None:
            self._item1 = self._add_item('item1')
        return self._item1

    @property
    def item2(self) -> ActionItemFake:
        if self._item2 is None:
            self._item2 = self._add_item('item2')
        return self._item2

    @property
    def item3(self) -> ActionItemFake:
        if self._item3 is None:
            self._item3 = self._add_item('item3')
        return self._item3

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
            self.action_manager.on_events = self._events.add
        return self._events


@pytest.fixture()
def fixture(clean_document):
    f = Fixture()
    f.action_manager.install()
    try:
        yield f
    finally:
        f.action_manager.uninstall()
