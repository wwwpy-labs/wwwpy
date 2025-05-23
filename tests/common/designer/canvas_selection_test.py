from wwwpy.common.designer.canvas_selection import CanvasSelection, CanvasSelectionChangeEvent
from wwwpy.common.designer.html_locator import html_to_node_path
from wwwpy.common.designer.locator import Locator, Origin


def _new_element_path_old():
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    ep = Locator('p1.comp1', 'Comp2', node_path, Origin.source)
    return ep


def _new_element_path(class_module, class_name, html, path, origin):
    return Locator(class_module, class_name, html_to_node_path(html, path), origin)


_some_element_path = _new_element_path('p1.comp1', 'Comp2', "<br>", [0], Origin.source)


def test_initial_state():
    # GIVEN
    target = CanvasSelection()

    # WHEN

    # THEN
    assert target.current_selection is None


def test_assignment_should_stick():
    # GIVEN
    target = CanvasSelection()
    ep = _new_element_path_old()

    # WHEN
    target.current_selection = ep

    # THEN
    assert target.current_selection is ep


def test_events():
    # GIVEN
    target = CanvasSelection()
    ep1 = _new_element_path_old()
    ep2 = _new_element_path('p1.comp1', 'Comp2', "<br>", [0], Origin.source)
    events = []
    target.on_change.add(lambda e: events.append(e))

    # WHEN
    target.current_selection = ep1

    # THEN
    assert events == [CanvasSelectionChangeEvent(None, ep1)]
    events.clear()

    # WHEN
    target.current_selection = ep2

    # THEN
    assert events == [CanvasSelectionChangeEvent(ep1, ep2)]
    events.clear()

    # WHEN
    target.current_selection = None

    # THEN
    assert events == [CanvasSelectionChangeEvent(ep2, None)]
