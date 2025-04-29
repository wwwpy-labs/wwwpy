from __future__ import annotations

import logging

from pyodide.ffi import create_proxy

from wwwpy.remote.designer.ui.palette import PaletteItemComponent

logger = logging.getLogger(__name__)

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
