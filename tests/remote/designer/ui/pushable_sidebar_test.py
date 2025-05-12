import logging

import js

from wwwpy.common.designer.ui.rect_readonly import rect_to_py
from wwwpy.remote.designer.ui.pushable_sidebar import PushableSidebar

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
