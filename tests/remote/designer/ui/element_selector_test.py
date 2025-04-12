import logging

import js
import pytest

from wwwpy.remote.designer.ui.element_selector import ElementSelector
from wwwpy.remote.jslib import waitAnimationFrame

logger = logging.getLogger(__name__)


class TestElementSelector:
    async def test_selected_element_should_be_highlighted(self, target, div1):
        # GIVEN
        # set absolute position to div1
        # div1 = js.document.createElement('div')
        # js.document.body.append(div1)
        div1.style.position = 'absolute'
        div1.style.top = '30px'
        div1.style.left = '40px'
        div1.style.width = '100px'
        div1.style.height = '70px'
        # set border red
        div1.style.border = '2px solid red'

        # WHEN
        target.set_selected_element(div1)

        # THEN
        # check that the highlight overlay is shown and that it has the same size as div1
        assert target.highlight_overlay.visible
        dr = div1.getBoundingClientRect()
        expect = (dr.top, dr.left, dr.width, dr.height)
        actual = target.highlight_overlay.last_rect_tuple
        assert actual == expect

    async def test_move_element_should_update_highlight(self, target, div1):
        # todo, now add test after moving the element (implementation may use a ResizeObserver)
        # GIVEN
        # set absolute position to div1
        div1.style.position = 'absolute'
        div1.style.top = '30px'
        div1.style.left = '40px'
        div1.style.width = '100px'
        div1.style.height = '70px'
        # set border red
        div1.style.border = '2px solid red'

        target.set_selected_element(div1)

        # WHEN
        # move the element
        div1.style.top = '1px'
        div1.style.left = '2px'
        div1.style.width = '60px'
        div1.style.height = '70px'
        await waitAnimationFrame()

        # THEN
        # check that the highlight overlay is shown and that it has the same size as div1
        assert target.highlight_overlay.visible
        dr = div1.getBoundingClientRect()
        expect = (dr.top, dr.left, dr.width, dr.height)
        actual = target.highlight_overlay.last_rect_tuple
        assert actual == expect



class Fixture:
    def __init__(self):
        self.target = ElementSelector()
        js.document.body.append(self.target.element)
        self._div1 = None

    @property
    def div1(self):
        if not self._div1:
            self._div1 = js.document.createElement('div')
            js.document.body.append(self._div1)
        return self._div1


@pytest.fixture
def div1(fixture):
    return fixture.div1


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
