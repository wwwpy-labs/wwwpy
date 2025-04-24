import logging
from dataclasses import dataclass

import js
import pytest
from pyodide.ffi import create_proxy

from tests.remote.remote_fixtures import clean_document
from tests.remote.rpc4tests_helper import rpctst_exec

logger = logging.getLogger(__name__)


# credits https://www.martin-grandrath.de/blog/2024-05-01_testing-touch-gestures-with-playwright.html

async def test_touch_event(div1):
    # GIVEN
    rect = div1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    logger.debug(f'GIVEN phase done x={x} y={y}')

    events = []
    div1.addEventListener('touchstart', create_proxy(lambda e: events.append(e)))
    # WHEN

    await rpctst_exec(
        'pwb.cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{'  f'"x": {x}, "y": {y}' '}]})'
    )

    assert events != []
    assert len(events) == 1
    event = events[0]
    assert event.type == 'touchstart'
    assert event.target.id == 'div1'
    item0 = event.touches.item(0)
    assert item0.clientX == x
    assert item0.clientY == y


@pytest.fixture()
def fixture(clean_document):
    yield Fixture()


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
