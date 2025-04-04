from dataclasses import dataclass, field

import js
import pytest

from wwwpy.remote.designer.ui.palette import GestureEvent, ActionManager, PaletteComponent, PaletteItemComponent
from wwwpy.server.rpc4tests import rpctst_exec


async def test_palette_no_selected_item(action_manager):
    assert action_manager.selected_item is None


async def test_palette_click_item__should_be_selected(palette, action_manager):
    item = palette.add_item('item1-key', 'item1')
    item.element.click()

    assert action_manager.selected_item == item
    assert item.selected


async def test_palette_click_twice_item__should_be_deselected(palette, action_manager):
    item = palette.add_item('item1-key', 'item1')
    item.element.click()
    item.element.click()

    assert action_manager.selected_item is None
    assert not item.selected


async def test_palette_selecting_different_item__should_deselect_previous(palette, action_manager):
    item1 = palette.add_item('item1-key', 'item1')
    item2 = palette.add_item('item2-key', 'item2')
    item1.element.click()
    item2.element.click()

    assert action_manager.selected_item == item2
    assert not item1.selected
    assert item2.selected


async def test_palette_should_put_elements_on_screen(palette):
    item1 = palette.add_item('item1-key', 'item1')
    item2 = palette.add_item('item2-key', 'item2')
    item3 = palette.add_item('item3-key', 'item3')

    assert item1.element.isConnected is True
    assert item2.element.isConnected is True
    assert item3.element.isConnected is True


async def test_externally_select_item(palette, action_manager):
    item1 = palette.add_item('item1-key', 'item1')
    item2 = palette.add_item('item2-key', 'item2')

    action_manager.selected_item = item1

    assert action_manager.selected_item == item1
    assert item1.selected


async def test_externally_select_different_item(palette, action_manager):
    item1 = palette.add_item('item1-key', 'item1')
    item2 = palette.add_item('item2-key', 'item2')

    action_manager.selected_item = item1
    action_manager.selected_item = item2

    assert action_manager.selected_item == item2
    assert not item1.selected
    assert item2.selected


async def test_externally_deselect_item(palette):
    item1 = palette.add_item('item1-key', 'item1')
    item2 = palette.add_item('item2-key', 'item2')

    palette.selected_item = item1
    palette.selected_item = None

    assert palette.selected_item is None
    assert not item1.selected


class TestUseSelection:
    def test_selection_and_click__reject_should_not_deselect(self, palette, action_manager):
        # GIVEN
        item1 = palette.add_item('item1-key', 'item1')
        palette.selected_item = item1
        accept_calls = []

        def destination_accept(gesture_event):
            accept_calls.append(gesture_event)
            return False

        action_manager.destination_accept = destination_accept

        js.document.body.insertAdjacentHTML('beforeend', '<div id="div1">hello</div>')

        # WHEN
        js.document.getElementById('div1').click()

        # THEN
        assert len(accept_calls) == 1
        assert palette.selected_item is item1

    async def test_selection_and_click__accept_should_deselect(self, palette, action_manager):
        # GIVEN
        item1 = palette.add_item('item1-key', 'item1')
        action_manager.selected_item = item1
        accept_calls = []

        def destination_accept(gesture_event: GestureEvent):
            accept_calls.append(gesture_event)
            gesture_event.accept()

        action_manager.destination_accept = destination_accept

        js.document.body.insertAdjacentHTML('beforeend', '<div id="div1">hello</div>')

        # WHEN
        js.document.getElementById('div1').click()

        # THEN
        # await asyncio.sleep(100000)
        assert len(accept_calls) == 1
        assert action_manager.selected_item is None


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

    async def test_selected_drag__accepted_should_deselect(self, palette, action_manager):
        # GIVEN
        item1 = palette.add_item('item1-key', 'item1')
        item1.element.id = 'item1'
        action_manager.selected_item = item1
        js.document.body.insertAdjacentHTML('beforeend', '<div id="div1">hello</div>')
        action_manager.destination_accept = lambda event: event.accept()

        # WHEN
        await rpctst_exec("page.locator('#item1').drag_to(page.locator('#div1'))")

        # THEN
        assert action_manager.selected_item is None
        assert not item1.selected


@pytest.fixture
def palette(fixture):
    yield fixture.palette


@pytest.fixture
def action_manager(fixture):
    yield fixture.action_manager


@dataclass
class Fixture:
    palette: PaletteComponent = field(default_factory=PaletteComponent)
    action_manager: ActionManager = field(default_factory=ActionManager)

    def __post_init__(self):
        self.palette.action_manager = self.action_manager


@pytest.fixture()
def fixture():
    try:
        f = Fixture()
        js.document.body.innerHTML = ''
        js.document.body.appendChild(f.palette.element)
        yield f
    finally:
        js.document.body.innerHTML = ''
