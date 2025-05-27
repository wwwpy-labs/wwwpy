import logging

import js
import pytest

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js
from wwwpy.remote._elementlib import element_xy_center
from wwwpy.remote.jslib import is_contained, is_instance_of, get_deepest_element

logger = logging.getLogger(__name__)


class NestedHtmlFixture:
    def __init__(self):
        js.document.body.innerHTML = """<div id="outer"><div id="inner"></div></div><div id="other"></div>"""
        self.outer = js.document.getElementById('outer')
        self.inner = js.document.getElementById('inner')
        self.other = js.document.getElementById('other')


@pytest.fixture
def nested_html_fixture():
    return NestedHtmlFixture()


@pytest.fixture
def outer(nested_html_fixture):
    return nested_html_fixture.outer


@pytest.fixture
def inner(nested_html_fixture):
    return nested_html_fixture.inner


@pytest.fixture
def other(nested_html_fixture):
    return nested_html_fixture.other


class Test_is_contained():

    async def test_simple_contained(self, outer, inner):
        assert is_contained(inner, outer)

    async def test_container_itself(self, outer):
        assert is_contained(outer, outer)

    async def test_not_contained(self, outer, other):
        assert not is_contained(other, outer)

    async def test_reproduce_issue_20250412(self):
        class SlottedComponent(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        class CompRoot(wpc.Component):
            slotted1: SlottedComponent = wpc.element()
            inner: js.HTMLElement = wpc.element()

            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                # we avoid naming the component so we don't clash with other tests
                snippet = (SlottedComponent.component_metadata
                           .build_snippet({'data-name': 'slotted1'}, '<span><div data-name="inner"></div></span>'))
                self.element.shadowRoot.innerHTML = snippet

        root = CompRoot()
        js.document.body.append(root.element)

        slotted1 = root.slotted1.element
        inner = root.inner
        assert is_contained(inner, slotted1)

    async def test_issue_with__accessing_host_attr(self):
        # anchors has a property 'host'

        js.document.body.innerHTML = "<div id='outer'><a id='inner' href='https://some-host'>some</a></div>"
        outer = js.document.getElementById('outer')
        inner = js.document.getElementById('inner')
        assert is_contained(inner, outer)

    async def test_with_shadow_on_outer(self, outer):
        shadow = outer.attachShadow(dict_to_js({'mode': 'open'}))
        shadow.innerHTML = '<div id="shadow"></div>'
        shadow_div = shadow.getElementById('shadow')
        assert is_contained(shadow_div, outer)

    async def test_with_shadow_on_inner(self, inner):
        shadow = inner.attachShadow(dict_to_js({'mode': 'open'}))
        shadow.innerHTML = '<div id="shadow"></div>'
        shadow_div = shadow.getElementById('shadow')
        assert is_contained(shadow_div, inner)

    async def test_with_slots(self):
        class Comp1(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        inner_list = []

        class Comp11(wpc.Component):
            inner: js.HTMLElement = wpc.element()

            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<div data-name="inner"></div>'
                inner_list.append(self.inner)

        snippet = Comp1.component_metadata.build_snippet({'id': 'outer'}, Comp11.component_metadata.html_snippet)
        logger.debug(f'snippet: `{snippet}`')
        js.document.body.innerHTML = snippet
        outer = js.document.getElementById('outer')
        assert len(inner_list) == 1
        inner = inner_list[0]
        assert is_contained(inner, outer)

    async def test_with_slots_triple(self):
        class Comp0(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        js.document.body.innerHTML = Comp0.component_metadata.build_snippet({},
                                                                            "<span id='outer'><div id='inner'></div></span>")
        outer = js.document.getElementById('outer')
        inner = js.document.getElementById('inner')
        assert is_contained(inner, outer)


class Test_is_contained_lambda():

    async def test_lambda(self, inner):
        assert is_contained(inner, lambda x: x.id == 'outer')

    async def test_document(self, failure_fixture, inner):
        """We reach js.HTMLDocument, but it should not be passed to the lambda."""
        assert not is_contained(inner, failure_fixture.is_container)
        assert failure_fixture.failures == []

    async def test_shadow(self, failure_fixture, inner):
        shadow = inner.attachShadow(dict_to_js({'mode': 'open'}))
        shadow.innerHTML = '<div id="shadow"></div>'

        assert not is_contained(inner, failure_fixture.is_container)

        assert failure_fixture.failures == []


class FailureFixture:
    def __init__(self):
        self.failures = []

    def is_container(self, x):
        if not hasattr(x, 'tagName'):
            fail = f'element should not be passed `{dict_to_js(x)}`'
            self.failures.append(fail)
        return False


@pytest.fixture
def failure_fixture():
    return FailureFixture()


class Test_is_instance_of():
    async def test_is_instance_of(self):
        assert is_instance_of(js.document, js.HTMLDocument)


class Test_get_deepest_element:

    async def test_simple_div(self):
        js.document.body.innerHTML = """<div id="outer">div-outer</div>"""
        outer = js.document.getElementById('outer')
        x, y = element_xy_center(outer)
        element = get_deepest_element(x, y)
        assert element == outer

    async def test_coordinates_that_coincide_with_div(self):
        class Comp1(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<div id="shadow">shadow</div>'

        comp1 = Comp1()
        js.document.body.append(comp1.element)
        x, y = element_xy_center(comp1.element)
        actual = get_deepest_element(x, y)
        expect = comp1.element.shadowRoot.getElementById('shadow')

        assert actual == expect

    async def test_coordinates_that_has_only_the_shadow_dom_itself(self):
        class Comp1(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = 'shadow'

        comp1 = Comp1()
        js.document.body.append(comp1.element)

        # await asyncio.sleep(100000)

        x, y = element_xy_center(comp1.element)
        actual = get_deepest_element(x, y)
        expect = comp1.element
        assert actual == expect

    def test_nothing_at_coordinates(self):
        actual = get_deepest_element(1, 1)
        assert is_instance_of(actual, js.HTMLHtmlElement), f'Expected HTMLHtmlElement, got {type(actual)}'
