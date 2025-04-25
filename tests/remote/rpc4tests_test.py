import logging
from dataclasses import dataclass

import js
import pytest
from pyodide.ffi import create_proxy, create_once_callable

from tests.remote.remote_fixtures import clean_document
from tests.remote.rpc4tests_helper import rpctst_exec_touch_event
from wwwpy.remote._elementlib import element_xy_center

logger = logging.getLogger(__name__)


# credits https://www.martin-grandrath.de/blog/2024-05-01_testing-touch-gestures-with-playwright.html

async def test_touch_apis__touchend(div1):
    # GIVEN
    events = await _handle_touch_events(div1)
    x, y = element_xy_center(div1)

    # WHEN
    await _send_touch_events(x, y, x + 20, y + 20)

    # THEN
    types = list(map(lambda e: e.type, events))
    logger.debug(f'types={types}')
    assert types == ['touchstart', 'touchmove', 'touchend']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']
    _verify_xy(events[0], x, y)
    _verify_xy(events[1], x + 20, y + 20)


async def test_touch_apis__touchcancel(div1):
    # GIVEN
    events = await _handle_touch_events(div1)
    x, y = element_xy_center(div1)

    # WHEN
    await _send_touch_events(x, y, x + 20, y + 20, cancel=True)

    # THEN
    types = list(map(lambda e: e.type, events))
    logger.debug(f'types={types}')
    assert types == ['touchstart', 'touchmove', 'touchcancel']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']
    _verify_xy(events[0], x, y)
    _verify_xy(events[1], x + 20, y + 20)


async def test_pointer_apis__pointercancel(div1):
    # GIVEN
    events = await _handle_pointer_events(div1)
    x, y = element_xy_center(div1)

    # WHEN
    await _send_touch_events(x, y, x + 20, y + 20)

    # THEN
    types = list(map(lambda e: e.type, events))
    logger.debug(f'types={types}')
    assert types == ['pointerdown', 'pointermove', 'pointercancel']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']


async def test_pointer_apis__pointerup(div1):
    # GIVEN
    events = await _handle_pointer_events(div1)
    x, y = element_xy_center(div1)

    # WHEN
    await _send_touch_events(x, y, x + 5, y + 5)

    # THEN
    types = list(map(lambda e: e.type, events))
    logger.debug(f'types={types}')
    assert types == ['pointerdown', 'pointermove', 'pointerup']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']


def _verify_xy(event, x, y):
    __tracebackhide__ = True
    item0 = event.touches.item(0)
    assert item0.clientX == x
    assert item0.clientY == y


async def _handle_pointer_events(div1):
    events = []
    div1.addEventListener('pointerdown', create_proxy(events.append))
    div1.addEventListener('pointermove', create_proxy(events.append))
    div1.addEventListener('pointerup', create_proxy(events.append))
    div1.addEventListener('pointercancel', create_proxy(events.append))
    return events


async def _handle_touch_events(div1):
    events = []
    div1.addEventListener('touchstart', create_proxy(events.append))
    div1.addEventListener('touchmove', create_proxy(events.append))
    div1.addEventListener('touchend', create_proxy(events.append))
    div1.addEventListener('touchcancel', create_proxy(events.append))
    return events


async def _send_touch_events(x, y, move_x, move_y, cancel=False):
    await rpctst_exec_touch_event([
        {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]},
        # touchmove event will only trigger when there's significant enough movement to be detected as an intentional gesture
        {'type': 'touchMove', 'touchPoints': [{'x': move_x, 'y': move_y}]},
        {'type': 'touchEnd' if not cancel else 'touchCancel', 'touchPoints': []},
    ])


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
