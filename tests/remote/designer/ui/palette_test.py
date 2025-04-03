import js
import pytest

from wwwpy.remote.designer.ui import palette  # noqa - import custom element


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



@pytest.fixture
def target():
    target = palette.PaletteComponent()
    js.document.body.innerHTML = ''
    js.document.body.appendChild(target.element)
    try:
        yield target
    finally:
        js.document.body.innerHTML = ''
