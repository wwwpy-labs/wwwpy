from __future__ import annotations

import js

from wwwpy.common.designer.ui.rect_readonly_py import RectReadOnlyPy
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.designer.ui.tool_selection_indicator import SelectionIndicatorTool


def test_simple():
    # GIVEN
    target = SelectionIndicatorTool()
    rect = RectReadOnlyPy(22, 11, 40, 20)
    rect_center = rect.xy_center
    target.set_reference_geometry(rect)

    # WHEN
    js.document.body.append(target.element)
    element_center = element_xy_center(target.element)

    # THEN
    assert rect_center == element_center

    rect_area = rect.width * rect.height
    element_area = target.element.clientWidth * target.element.clientHeight
    assert rect_area * 0.9 < element_area < rect_area * 1.1
