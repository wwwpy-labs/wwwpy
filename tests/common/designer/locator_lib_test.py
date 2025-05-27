# without the following the component_fixture fails with `E fixture 'dyn_sys_path' not found`
from tests.common import dyn_sys_path, DynSysPath  # noqa
from tests.common.designer.component_fixture import ComponentFixture, component_fixture
from wwwpy.common.designer.html_locator import html_to_node_path
from wwwpy.common.designer.locator_lib import Locator, Origin, rebase_to_origin


def test_valid__path_to_component(component_fixture: ComponentFixture):
    html = """<button>bar</button>"""
    component_fixture.write_component('p1/comp1.py', 'Comp1', html=html)
    node_path = html_to_node_path(html, [0])
    target = Locator('p1.comp1', 'Comp1', node_path, Origin.source)
    assert target.valid()


def test_valid___path_to_component__not_valid_node_path(component_fixture: ComponentFixture):
    component_fixture.write_component('p1/comp1.py', 'Comp1', html="")
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    target = Locator('p1.comp1', 'Comp1', node_path, Origin.source)
    assert not target.valid()


def test_valid__class_do_not_exist(component_fixture: ComponentFixture):
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    target = Locator('p2.comp2', 'Comp2', node_path, Origin.source)
    assert not target.valid()


def test_valid__file_exists_but_class_do_not(component_fixture: ComponentFixture):
    component_fixture.write_component('p1/comp1.py', 'Comp1', html="")
    node_path = html_to_node_path("""<button>bar</button>""", [0])
    target = Locator('p1.comp1', 'Comp2', node_path, Origin.source)
    assert not target.valid()


class TestRebaseToOrigin:
    def test_regular_component(self, component_fixture: ComponentFixture):
        # GIVEN
        html = """<span style="color: red;">Hello</span>"""
        component_fixture.write_component('p1/comp1.py', 'Comp1', html=html)
        # could be different because of live/runtime changes
        different_node_path = html_to_node_path("""<span>Hello12</span>""", [0])
        locator = Locator('p1.comp1', 'Comp1', different_node_path, Origin.live)

        # WHEN
        rebased = rebase_to_origin(locator)

        # THEN
        assert rebased is not None
        assert rebased.class_module == 'p1.comp1'
        assert rebased.class_name == 'Comp1'
        assert rebased.path == html_to_node_path(html, [0])

    def test_empty_html(self, component_fixture: ComponentFixture):
        # GIVEN
        component_fixture.write_component('p1/comp1.py', 'Comp1', html="")
        locator = Locator('p1.comp1', 'Comp1', [], Origin.live)

        # WHEN
        rebased = rebase_to_origin(locator)

        # THEN
        assert rebased is not None
        assert rebased.class_module == 'p1.comp1'
        assert rebased.class_name == 'Comp1'
        assert rebased.path == []
        assert rebased.origin == Origin.source

    def test_nonexistent_component(self, component_fixture: ComponentFixture):
        # GIVEN
        locator = Locator('p1.comp1', 'Comp1', [], Origin.live)

        # WHEN
        rebased = rebase_to_origin(locator)

        # THEN
        assert rebased is None
