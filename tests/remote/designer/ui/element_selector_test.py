import logging

import js
import pytest

from wwwpy.remote import dict_to_py
from wwwpy.remote.designer.ui.element_selector import ElementSelector
from wwwpy.remote.jslib import waitAnimationFrame

logger = logging.getLogger(__name__)


class TestElementSelector:
    async def test_selected_element_should_be_highlighted(self, target, div1):
        # GIVEN
        # div1

        # WHEN
        target.set_selected_element(div1)
        await waitAnimationFrame()

        # THEN
        _assert_geometry_ok(div1, target)

    async def test_resize_element_should_update_highlight(self, target, div1):
        # GIVEN
        # div1 and
        target.set_selected_element(div1)

        # WHEN
        # move the element
        div1.style.width = '50px'
        div1.style.height = '60px'
        await waitAnimationFrame()

        # THEN
        _assert_geometry_ok(div1, target)

    async def test_move_element_should_update_highlight(self, target, div1):
        # GIVEN
        # div1 and
        target.set_selected_element(div1)
        await waitAnimationFrame()

        # WHEN
        # move the element
        div1.style.top = '50px'
        div1.style.left = '60px'
        await waitAnimationFrame()

        # THEN
        _assert_geometry_ok(div1, target)

    async def test_move_by_another_element(self, target, div1, div2):
        # GIVEN
        # div1 and div2
        target.set_selected_element(div2)
        await waitAnimationFrame()

        # WHEN
        # move div2 trough div1
        div1.style.top = '50px'
        div1.style.left = '60px'
        await waitAnimationFrame()

        # THEN
        _assert_geometry_ok(div2, target)

    async def test_set_inner_element_should_raise(self, target):
        # GIVEN
        inner_elements = (target.element,
                          target.highlight_overlay.element,
                          target.toolbar_button.element,
                          ) + tuple(target.toolbar_button.element.shadowRoot.children)

        for ele in inner_elements:
            logger.debug(f'inner element: `{dict_to_py(ele)}`')
            with pytest.raises(ValueError):
                target.set_selected_element(ele)


def _assert_geometry_ok(div1, target):
    dr = div1.getBoundingClientRect()
    expect = (dr.top, dr.left, dr.width, dr.height)
    actual = target._last_position
    assert actual == expect


class Fixture:
    def __init__(self):
        self.target = ElementSelector()
        js.document.body.append(self.target.element)
        self._div1 = None
        self._div2 = None  # it will be child of div1

    @property
    def div1(self):
        if not self._div1:
            self._div1 = js.document.createElement('div')
            _setup_div(self._div1)
            js.document.body.append(self._div1)
        return self._div1

    @property
    def div2(self):
        if not self._div2:
            self._div2 = js.document.createElement('div')
            self.div1.appendChild(self._div2)
        return self._div2


def _setup_div(div1):
    div1.style.position = 'absolute'
    div1.style.top = '30px'
    div1.style.left = '40px'
    div1.style.width = '100px'
    div1.style.height = '70px'
    # set border red
    div1.style.border = '2px solid red'


@pytest.fixture
def div1(fixture):
    return fixture.div1


@pytest.fixture
def div2(fixture):
    return fixture.div2

@pytest.fixture
def target(fixture):
    return fixture.target


@pytest.fixture
def fixture():
    clean_browser()
    f = Fixture()
    yield f
    clean_browser()


def clean_browser():
    js.document.documentElement.innerHTML = ''
    js.document.head.innerHTML = ''
    for attr in js.document.documentElement.attributes:
        js.document.documentElement.removeAttributeNode(attr)
