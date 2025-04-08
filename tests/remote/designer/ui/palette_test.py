import logging
from dataclasses import dataclass, field
from typing import TypeVar

import js
import pytest

from wwwpy.remote.designer.ui.palette import ActionEvent, ActionManager, PaletteComponent, PaletteItemComponent, \
    PaletteItem, HoverEvent, DropEvent
from wwwpy.server.rpc4tests import rpctst_exec

logger = logging.getLogger(__name__)


async def test_palette_no_selected_item(action_manager):
    assert action_manager.selected_action is None


async def test_palette_click_item__should_be_selected(palette, action_manager, item1):
    item1.element.click()

    assert action_manager.selected_action == item1
    assert item1.selected


async def test_palette_click_twice_item__should_be_deselected(palette, action_manager, item1):
    item1.element.click()
    item1.element.click()

    assert action_manager.selected_action is None
    assert not item1.selected


async def test_palette_selecting_different_item__should_deselect_previous(palette, action_manager, item1, item2):
    item1.element.click()
    item2.element.click()

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
    action_manager.selected_action = item1
    action_manager.selected_action = item2

    assert action_manager.selected_action == item2
    assert not item1.selected
    assert item2.selected


async def test_externally_deselect_item(palette, item1, item2):
    palette.selected_item = item1
    palette.selected_item = None

    assert palette.selected_item is None
    assert not item1.selected


class TestUseSelection:
    def test_selection_and_click__reject_should_not_deselect(self, palette, action_manager, item1, div1):
        # GIVEN
        palette.selected_item = item1
        accept_calls = []

        def destination_accept(gesture_event):
            accept_calls.append(gesture_event)
            return False

        action_manager.on_events = destination_accept

        # WHEN
        js.document.getElementById('div1').click()

        # THEN
        assert len(accept_calls) == 1
        assert palette.selected_item is item1

    async def test_selection_and_click__accept_should_deselect(self, palette, action_manager, item1, div1):
        # GIVEN
        action_manager.selected_action = item1
        accept_calls = []

        def destination_accept(gesture_event: ActionEvent):
            accept_calls.append(gesture_event)
            gesture_event.spend()

        action_manager.on_events = destination_accept

        # WHEN
        js.document.getElementById('div1').click()

        # THEN
        # await asyncio.sleep(100000)
        assert len(accept_calls) == 1
        assert action_manager.selected_action is None


class TestPaletteItem:

    def test_selected_should_have_class_selected(self):
        item = PaletteItemComponent()
        item.selected = True
        assert item.element.classList.contains('selected')

    def test_selected_deselected_should_not_have_class_selected(self):
        item = PaletteItemComponent()
        item.selected = True
        item.selected = False
        assert not item.element.classList.contains('selected')


class TestDrag:
    # see Playwright cancel drag here https://github.com/danielwiehl/playwright-bug-reproducer-dnd-cancel/blob/master/tests/reproducer.spec.ts
    # and generally https://chatgpt.com/share/67efcda6-9890-8006-8542-3634aa9249bf

    async def test_selected_drag__accepted_should_deselect(self, palette, action_manager, item1, div1):
        # GIVEN
        action_manager.selected_action = item1
        action_manager.on_events = lambda event: event.spend()

        # WHEN
        await rpctst_exec("page.locator('#item1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None
        assert not item1.selected

    async def TODO_test_no_selection_drag_and_drop__should_emit_Drag(self, palette, action_manager, item1, div1,
                                                                     events):
        # GIVEN
        #

        # WHEN
        await rpctst_exec("page.locator('#item1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_action is None

        assert len(events.drop_events) == 1, 'one drag event expected'
        assert events.drop_events[0].drop_target is div1


class TestHover:

    async def test_selected_and_hover_on_palette__should_not_emit_Hover(self, palette, action_manager, item1, item2):
        # GIVEN
        action_manager.selected_action = item1

        def on_events(event: ActionEvent):
            if isinstance(event, HoverEvent):
                raise Exception(f'hover not expected {event}')

        action_manager.on_events = on_events

        # WHEN
        await rpctst_exec("page.locator('#item2').hover()")

        # THEN
        assert action_manager.selected_action is item1  # should still be selected

    async def test_selected_and_hover_on_div1__should_emit_Hover(self, palette, action_manager, item1, div1):
        # GIVEN
        action_manager.selected_action = item1
        events = []

        def on_events(event: ActionEvent):
            events.append(event)

        action_manager.on_events = on_events

        # WHEN
        await rpctst_exec("page.locator('#div1').hover()")

        # THEN
        assert action_manager.selected_action is item1  # should still be selected

        hover_events = [event for event in events if isinstance(event, HoverEvent)]
        logger.debug(f'hover_events={hover_events}')
        assert hover_events != [], 'hover event not emitted'
        # assert hover_events[0].dragging is False

    async def test_drag_and_hover_on_div1__should_emit_Hover(self, palette, action_manager, item1, div1):
        # GIVEN
        action_manager.selected_action = item1
        events = []

        def on_events(event: ActionEvent):
            events.append(event)

        action_manager.on_events = on_events

        # WHEN
        page_commands = ["page.locator('#item1').hover()", "page.mouse.down()", "page.locator('#div1').hover()"]
        for page_cmd in page_commands: await rpctst_exec(page_cmd)

        # THEN
        hover_events = [event for event in events if isinstance(event, HoverEvent)]
        logger.debug(f'hover_events={hover_events}')
        assert hover_events != [], 'hover event not emitted'
        # assert hover_events[0].dragging is True


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


_AE = TypeVar('_AE', bound=ActionEvent)


class EventFixture:
    def __init__(self):
        self._events = []

    def add(self, event):
        self._events.append(event)

    def filter(self, event_type: type[_AE]) -> list[_AE]:
        return [event for event in self._events if isinstance(event, event_type)]

    @property
    def drop_events(self) -> list[DropEvent]:
        return self.filter(DropEvent)

@dataclass
class Fixture:
    palette: PaletteComponent = field(default_factory=PaletteComponent)
    action_manager: ActionManager = field(default_factory=ActionManager)
    _events: EventFixture = None
    _item1: PaletteItem = None
    _item2: PaletteItem = None
    _item3: PaletteItem = None
    _div1: js.HTMLDivElement = None

    def __post_init__(self):
        self.palette.action_manager = self.action_manager

    def _add_item(self, label: str) -> PaletteItem:
        item = self.palette.add_item(f'{label}-key', label)
        item.element.id = label
        return item

    @property
    def item1(self) -> PaletteItem:
        if self._item1 is None:
            self._item1 = self._add_item('item1')
        return self._item1

    @property
    def item2(self) -> PaletteItem:
        if self._item2 is None:
            self._item2 = self._add_item('item2')
        return self._item2

    @property
    def item3(self) -> PaletteItem:
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
def fixture():
    try:
        f = Fixture()
        js.document.body.innerHTML = ''
        js.document.body.appendChild(f.palette.element)
        yield f
    finally:
        js.document.body.innerHTML = ''
