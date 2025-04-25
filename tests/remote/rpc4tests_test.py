import asyncio
import logging
from dataclasses import dataclass

import js
import pytest
from pyodide.ffi import create_proxy, create_once_callable

from tests.remote.remote_fixtures import clean_document
from tests.remote.rpc4tests_helper import rpctst_exec_touch_event
from wwwpy.remote.jslib import waitAnimationFrame

logger = logging.getLogger(__name__)


# credits https://www.martin-grandrath.de/blog/2024-05-01_testing-touch-gestures-with-playwright.html

async def test_touch_apis(div1):
    # GIVEN
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    logger.debug(f'GIVEN phase done x={x} y={y}')

    events = []
    div1.addEventListener('touchstart', create_proxy(events.append))
    div1.addEventListener('touchmove', create_proxy(events.append))
    div1.addEventListener('touchend', create_proxy(events.append))

    # WHEN
    await rpctst_exec_touch_event([
        {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]},
        # touchmove event will only trigger when there's significant enough movement to be detected as an intentional gesture
        {'type': 'touchMove', 'touchPoints': [{'x': x + 20, 'y': y + 20}]},
        {'type': 'touchEnd', 'touchPoints': []},
    ])

    # THEN
    types = list(map(lambda e: e.type, events))
    logger.debug(f'types={types}')
    assert types == ['touchstart', 'touchmove', 'touchend']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']
    _verify_xy(events[0], x, y)
    _verify_xy(events[1], x + 20, y + 20)


async def test_pointer_apis__cancel(div1):
    # GIVEN
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    logger.debug(f'GIVEN phase done x={x} y={y}')

    events = []
    div1.addEventListener('pointerdown', create_proxy(events.append))
    div1.addEventListener('pointermove', create_proxy(events.append))
    div1.addEventListener('pointerup', create_proxy(events.append))
    div1.addEventListener('pointercancel', create_proxy(events.append))

    # WHEN
    await rpctst_exec_touch_event([
        {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]},
        # touchmove event will only trigger when there's significant enough movement to be detected as an intentional gesture
        {'type': 'touchMove', 'touchPoints': [{'x': x + 20, 'y': y + 20}]},
        {'type': 'touchEnd', 'touchPoints': []},
    ])

    # THEN
    types = list(map(lambda e: e.type, events))
    logger.debug(f'types={types}')
    assert types == ['pointerdown', 'pointermove', 'pointercancel']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']



async def test_touch_on_pointer_api(div1):
    # GIVEN
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    logger.debug(f'GIVEN phase done x={x} y={y}')

    events = []
    div1.addEventListener('pointerdown', create_proxy(events.append))
    # div1.addEventListener('pointermove', create_proxy(events.append))
    div1.addEventListener('pointermove',
                          create_proxy(lambda e: [events.append(e), e.target.setPointerCapture(e.pointerId), ]))
    div1.addEventListener('pointerup', create_proxy(events.append))

    # WHEN
    await rpctst_exec_touch_event([
        {
            'type': 'touchStart',
            'touchPoints': [{
                'x': x, 'y': y,
                'radiusX': 2.5, 'radiusY': 2.5,
                'rotationAngle': 0,
                'force': 1,
                'id': 1
            }],
            'modifiers': 0
        },
        {
            'type': 'touchMove',
            'touchPoints': [{
                'x': x + 20, 'y': y + 20,
                'radiusX': 2.5, 'radiusY': 2.5,
                'rotationAngle': 0,
                'force': 1,
                'id': 1
            }],
            'modifiers': 0
        },
        {
            'type': 'touchEnd',
            'touchPoints': [],
            'modifiers': 0
        }
    ])
    # THEN
    types = list(map(lambda e: e.type, events))
    assert types == ['pointerdown', 'pointermove', 'pointerup']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']
    _verify_xy(events[0], x, y)
    _verify_xy(events[1], x + 20, y + 20)


async def test_touch_on_pointer_api_chatgpt(div1):
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2

    # div1.style.touchAction = 'none'
    events = []

    def on_down(e):
        e.target.setPointerCapture(e.pointerId)
        events.append(e)

    def on_up(e):
        e.target.releasePointerCapture(e.pointerId)
        events.append(e)
    div1.addEventListener('pointerdown', create_proxy(on_down))
    div1.addEventListener('pointermove', create_proxy(events.append))
    div1.addEventListener('pointerup', create_proxy(on_up))
    div1.addEventListener('pointercancel', create_proxy(events.append))

    await rpctst_exec_touch_event([
        {'type': 'touchStart',
         'touchPoints': [{'x': x, 'y': y, 'radiusX': 2.5, 'radiusY': 2.5, 'rotationAngle': 0, 'force': 1, 'id': 1}],
         'modifiers': 0},
        {'type': 'touchMove', 'touchPoints': [
            {'x': x + 20, 'y': y + 20, 'radiusX': 2.5, 'radiusY': 2.5, 'rotationAngle': 0, 'force': 1, 'id': 1}],
         'modifiers': 0},
        {'type': 'touchEnd', 'touchPoints': [], 'modifiers': 0}
    ])
    await waitAnimationFrame()

    types = [e.type for e in events]
    targets = [e.target.id for e in events]
    assert types == ['pointerdown', 'pointermove', 'pointerup']
    assert targets == ['div1', 'div1', 'div1']
    # _verify_xy(events[0], x,     y)
    # _verify_xy(events[1], x+20, y+20)


async def test_touch_on_pointer_api_merl(div1):
    # GIVEN
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    logger.debug(f'GIVEN phase done x={x} y={y}')

    events = []
    div1.addEventListener('pointerdown', create_proxy(events.append))
    # div1.addEventListener('pointermove', create_proxy(events.append))
    div1.addEventListener('pointermove', create_proxy(lambda e: [e.setPointerCapture(e.pointerId), events.append(e)]))
    div1.addEventListener('pointerup', create_proxy(events.append))

    # WHEN
    await rpctst_exec_touch_event([
        {
            'type': 'touchStart',
            'touchPoints': [{
                'x': x, 'y': y,
                'radiusX': 2.5, 'radiusY': 2.5,
                'rotationAngle': 0,
                'force': 1,
                'id': 1
            }],
            'modifiers': 0
        },
        {
            'type': 'touchMove',
            'touchPoints': [{
                'x': x + 20, 'y': y + 20,
                'radiusX': 2.5, 'radiusY': 2.5,
                'rotationAngle': 0,
                'force': 1,
                'id': 1
            }],
            'modifiers': 0
        },
        {
            'type': 'touchEnd',
            'touchPoints': [{  # Include the last touch point in touchEnd
                'x': x + 20, 'y': y + 20,
                'radiusX': 2.5, 'radiusY': 2.5,
                'rotationAngle': 0,
                'force': 1,
                'id': 1
            }],
            'modifiers': 0
        }
    ])

    # Add a small delay to ensure all events are processed
    await asyncio.sleep(0.1)

    # THEN
    types = list(map(lambda e: e.type, events))
    assert types == ['pointerdown', 'pointermove', 'pointerup']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']
    _verify_xy(events[0], x, y)
    _verify_xy(events[1], x + 20, y + 20)
    _verify_xy(events[2], x + 20, y + 20)  # Verify position of pointerup event

def _verify_xy(event, x, y):
    __tracebackhide__ = True
    item0 = event.touches.item(0)
    assert item0.clientX == x
    assert item0.clientY == y


async def test_touch_start(div1):
    # GIVEN
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    logger.debug(f'GIVEN phase done x={x} y={y}')

    events = []
    proxy = create_proxy(events.append)
    div1.addEventListener('touchstart', proxy)

    # WHEN
    await rpctst_exec_touch_event({'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})

    # THEN
    assert events != []
    assert len(events) == 1
    event = events[0]
    assert event.type == 'touchstart'
    assert event.target.id == 'div1'
    item0 = event.touches.item(0)
    assert item0.clientX == x
    assert item0.clientY == y
    div1.removeEventListener('touchstart', proxy)


@pytest.fixture()
def fixture(clean_document): yield Fixture()


@pytest.fixture
def div1(fixture): yield fixture.div1


@dataclass
class Fixture:
    _div1: js.HTMLDivElement = None

    @property
    def div1(self) -> js.HTMLDivElement:
        if self._div1 is None:
            self._div1 = js.document.createElement('div')
            self._div1.id = 'div1'
            self._div1.textContent = 'hello'
            js.document.body.appendChild(self._div1)
        return self._div1
