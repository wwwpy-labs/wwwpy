from wwwpy.common.designer.ui.py_rect_readonly import RectReadOnly


def test_rect_read_only_dc_instantiation_and_properties():
    rect = RectReadOnly(x=1.0, y=2.0, width=3.0, height=4.0)
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


def test_rect_read_only_dc_to_json():
    rect = RectReadOnly(x=1.0, y=2.0, width=3.0, height=4.0)
    json_data = rect.toJSON()

    # Should match DOMRectReadOnly.toJSON() structure
    assert json_data == {
        "x": 1.0,
        "y": 2.0,
        "width": 3.0,
        "height": 4.0
    }


def test_rect_read_only_init_from_instance():
    original = RectReadOnly(x=1.0, y=2.0, width=3.0, height=4.0)
    dup = RectReadOnly(original)
    assert dup.x == 1.0
    assert dup.y == 2.0
    assert dup.width == 3.0
    assert dup.height == 4.0
    assert dup.left == original.left
    assert dup.top == original.top
    assert dup.right == original.right
    assert dup.bottom == original.bottom


def test_rect_read_only_init_from_duck_typed_obj():
    class Dummy:
        def __init__(self, x, y, width, height):
            self.x = x
            self.y = y
            self.width = width
            self.height = height

    dummy = Dummy(5.0, 6.0, 7.0, 8.0)
    rect = RectReadOnly(dummy)
    assert rect.x == 5.0
    assert rect.y == 6.0
    assert rect.width == 7.0
    assert rect.height == 8.0
    assert rect.left == 5.0
    assert rect.top == 6.0
    assert rect.right == 12.0
    assert rect.bottom == 14.0
    assert rect.toJSON() == {"x": 5.0, "y": 6.0, "width": 7.0, "height": 8.0}
