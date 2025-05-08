from wwwpy.common.designer.ui.py_rect_readonly import RectReadOnlyDc


def test_rect_read_only_dc_instantiation_and_properties():
    rect = RectReadOnlyDc(x=1.0, y=2.0, width=3.0, height=4.0)
    # base properties
    assert rect.x == 1.0
    assert rect.y == 2.0
    assert rect.width == 3.0
    assert rect.height == 4.0
    # calculated edges
    assert rect.left == rect.x
    assert rect.top == rect.y
    assert rect.right == rect.x + rect.width
    assert rect.bottom == rect.y + rect.height
