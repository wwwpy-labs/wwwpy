import js

from wwwpy.remote.designer.ui import palette  # noqa - import custom element


async def test_palette_no_selected_item():
    target = palette.PaletteComponent()

    js.document.body.innerHTML = ''
    js.document.body.appendChild(target.element)

    assert target.selected_item is None


async def test_palette_():
    target = palette.PaletteComponent()

    js.document.body.innerHTML = ''
    js.document.body.appendChild(target.element)

    item = target.add_item('item1-key', 'item1')
    item.element.click()

    assert target.selected_item == item
