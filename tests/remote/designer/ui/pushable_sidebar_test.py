import logging

import js

import wwwpy.remote.component as wpc
from wwwpy.common.designer.ui.rect_readonly import rect_to_py
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.pushable_sidebar import PushableSidebar, is_inside_sidebar

logger = logging.getLogger(__name__)


async def test_default_should_be_left():
    target = PushableSidebar()
    js.document.body.appendChild(target.element)

    rect0 = target.element.getBoundingClientRect()
    logger.debug(f'rect0: {rect_to_py(rect0)}')
    assert rect0.width > 0
    assert rect0.height > 0
    assert rect0.x == 0
    assert rect0.y == 0


async def test_left_to_right():
    target = PushableSidebar()
    js.document.body.appendChild(target.element)

    rect0 = rect_to_py(target.element.getBoundingClientRect())
    logger.debug(f'rect0: {rect0}')

    # WHEN
    target.position = 'right'

    # THEN
    rect1 = rect_to_py(target.element.getBoundingClientRect())
    logger.debug(f'rect1: {rect1}')

    assert rect1.width > 0
    assert rect1.height > 0
    assert rect1.x > 0
    assert rect1.y == 0


async def test_to_right():
    target = PushableSidebar()
    target.position = 'right'
    js.document.body.appendChild(target.element)

    rect0 = target.element.getBoundingClientRect()
    logger.debug(f'rect0: {rect_to_py(rect0)}')
    assert rect0.width > 0
    assert rect0.height > 0
    assert rect0.x > 0
    assert rect0.y == 0


async def TODO_test_collapsed():
    # todo, the component need a lot of refactoring
    #  - should give a good way to disable animation so we can test it
    #  - should not use more the attributes instead of the dict
    #  - should not handle directly the keyboard double control (should be extracted somewhere else)
    target = PushableSidebar()
    js.document.body.appendChild(target.element)

    rect0 = rect_to_py(target.element.getBoundingClientRect())
    logger.debug(f'rect0: {rect0}')

    # WHEN
    target.state = 'collapsed'

    # THEN
    rect1 = rect_to_py(target.element.getBoundingClientRect())

    logger.debug(f'rect1: {rect1}')
    assert rect1.width < rect0.width
    assert rect1.height == rect0.height
    assert rect1.x == 0
    assert rect1.y == 0


async def test_is_inside_sidebar_true():
    target = PushableSidebar()
    inside = js.document.createElement('div')
    inside.innerHTML = 'foo'
    target.element.appendChild(inside)
    js.document.body.appendChild(target.element)

    assert is_inside_sidebar(inside) is True
    assert is_inside_sidebar(target.element) is True


async def test_is_inside_sidebar_true_internal_element():
    target = PushableSidebar()
    js.document.body.appendChild(target.element)

    assert is_inside_sidebar(target._sidebar_content) is True


async def test_is_inside_sidebar_nested_shadowdom():
    class Comp1(wpc.Component):
        inner = wpc.element()

        def init_component(self):
            self.element.attachShadow(dict_to_js({'mode': 'open'}))
            self.element.shadowRoot.innerHTML = """<div data-name="inner">foo</div>"""

    c1 = Comp1()
    target = PushableSidebar()
    target.element.appendChild(c1.element)
    js.document.body.appendChild(target.element)

    assert is_inside_sidebar(c1.element) is True
    assert is_inside_sidebar(c1.inner) is True


async def test_is_inside_sidebar_false():
    target = PushableSidebar()
    js.document.body.appendChild(target.element)

    outside = js.document.createElement('div')
    outside.innerHTML = 'bar'
    js.document.body.appendChild(outside)

    assert is_inside_sidebar(outside) is False
