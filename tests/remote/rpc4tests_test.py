import logging
from dataclasses import dataclass

import js
import pytest
from pyodide.ffi import create_proxy, create_once_callable

from tests.remote.remote_fixtures import clean_document
from tests.remote.rpc4tests_helper import rpctst_exec_touch_event

logger = logging.getLogger(__name__)


# credits https://www.martin-grandrath.de/blog/2024-05-01_testing-touch-gestures-with-playwright.html

async def test_touch_multiple(div1):
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
    assert types == ['touchstart', 'touchmove', 'touchend']
    targets = list(map(lambda e: e.target.id, events))
    assert targets == ['div1', 'div1', 'div1']
    _verify_xy(events[0], x, y)
    _verify_xy(events[1], x + 20, y + 20)


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
