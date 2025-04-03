import js
import pytest

from wwwpy.remote.designer.ui import palette  # noqa - import custom element
from wwwpy.remote.designer.ui.palette import GestureEvent


async def test_palette_no_selected_item(target):
    assert target.selected_item is None


async def test_palette_click_item__should_be_selected(target):
    item = target.add_item('item1-key', 'item1')
    item.element.click()

    assert target.selected_item == item
    assert item.selected


async def test_palette_click_twice_item__should_be_deselected(target):
    item = target.add_item('item1-key', 'item1')
    item.element.click()
    item.element.click()

    assert target.selected_item is None
    assert not item.selected


async def test_palette_selecting_different_item__should_deselect_previous(target):
    item1 = target.add_item('item1-key', 'item1')
    item2 = target.add_item('item2-key', 'item2')
    item1.element.click()
    item2.element.click()

    assert target.selected_item == item2
    assert not item1.selected
    assert item2.selected


async def test_palette_should_put_elements_on_screen(target):
    item1 = target.add_item('item1-key', 'item1')
    item2 = target.add_item('item2-key', 'item2')
    item3 = target.add_item('item3-key', 'item3')

    assert item1.element.isConnected is True
    assert item2.element.isConnected is True
    assert item3.element.isConnected is True


async def test_externally_select_item(target):
    item1 = target.add_item('item1-key', 'item1')
    item2 = target.add_item('item2-key', 'item2')

    target.selected_item = item1

    assert target.selected_item == item1
    assert item1.selected


async def test_externally_select_different_item(target):
    item1 = target.add_item('item1-key', 'item1')
    item2 = target.add_item('item2-key', 'item2')

    target.selected_item = item1
    target.selected_item = item2

    assert target.selected_item == item2
    assert not item1.selected
    assert item2.selected


async def test_externally_deselect_item(target):
    item1 = target.add_item('item1-key', 'item1')
    item2 = target.add_item('item2-key', 'item2')

    target.selected_item = item1
    target.selected_item = None

    assert target.selected_item is None
    assert not item1.selected


class TestUseSelection:
    def test_selection_and_click__reject_should_not_deselect(self, target):
        # GIVEN
        item1 = target.add_item('item1-key', 'item1')
        target.selected_item = item1
        accept_calls = []

        def destination_accept(gesture_event):
            accept_calls.append(gesture_event)
            return False

        target.destination_accept = destination_accept

        js.document.body.insertAdjacentHTML('beforeend', '<div id="div1">hello</div>')

        # WHEN
        js.document.getElementById('div1').click()

        # THEN
        assert len(accept_calls) == 1
        assert target.selected_item is item1

    async def test_selection_and_click__accept_should_deselect(self, target):
        # GIVEN
        item1 = target.add_item('item1-key', 'item1')
        target.selected_item = item1
        accept_calls = []

        def destination_accept(gesture_event: GestureEvent):
            accept_calls.append(gesture_event)
            gesture_event.accept()

        target.destination_accept = destination_accept

        js.document.body.insertAdjacentHTML('beforeend', '<div id="div1">hello</div>')

        # WHEN
        js.document.getElementById('div1').click()

        # THEN
        # await asyncio.sleep(100000)
        assert len(accept_calls) == 1
        assert target.selected_item is None


class TestPaletteItem:

    def test_selected_should_have_class_selected(self):
        item = palette.PaletteItemComponent()
        item.selected = True
        assert item.element.classList.contains('selected')

    def test_selected_deselected_should_not_have_class_selected(self):
        item = palette.PaletteItemComponent()
        item.selected = True
        item.selected = False
        assert not item.element.classList.contains('selected')


@pytest.fixture
def target():
    target = palette.PaletteComponent()
    js.document.body.innerHTML = ''
    js.document.body.appendChild(target.element)
    try:
        yield target
    finally:
        js.document.body.innerHTML = ''
