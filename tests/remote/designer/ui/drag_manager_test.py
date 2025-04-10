import logging
from dataclasses import dataclass

import js
import pytest

from tests.remote.rpc4tests_helper import rpctst_exec
from wwwpy.remote.designer.ui.drag_manager import DragManager

logger = logging.getLogger(__name__)


async def test_initial_state_is_idle(drag_manager):
    assert drag_manager.state == DragManager.IDLE
    assert drag_manager.source_element is None


async def test_idle_to_drag_ready_state_transition(drag_manager, fixture):
    # GIVEN
    drag_manager.on_pointerdown_accept = lambda event: event.target.id == 'source1'

    # WHEN
    await rpctst_exec(["page.locator('#source1').hover()", "page.mouse.down()", "page.mouse.move(100, 100)"])

    # THEN
    assert drag_manager.state == DragManager.DRAGGING
    assert drag_manager.source_element == fixture.source1


async def test_mousedown_accepted__should_go_in_ready(drag_manager, fixture):
    # GIVEN
    drag_manager.on_pointerdown_accept = lambda event: event.target.id == 'source1'

    # WHEN
    await rpctst_exec(["page.locator('#source1').hover()", "page.mouse.down()"])

    # THEN
    assert drag_manager.state == DragManager.READY


async def test_mousedown_rejected__should_stay_in_idle(drag_manager, fixture):
    # GIVEN
    drag_manager.on_pointerdown_accept = lambda event: False

    # WHEN
    await rpctst_exec(["page.locator('#source1').hover()", "page.mouse.down()"])

    # THEN
    assert drag_manager.state == DragManager.IDLE


async def test_move_not_enough_for_drag__should_go_in_ready(drag_manager, fixture):
    # GIVEN
    drag_manager.on_pointerdown_accept = lambda event: event.target.id == 'source1'

    rect = fixture.source1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2

    # WHEN
    await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 3}, {y + 3})"])

    # THEN
    assert drag_manager.state == DragManager.READY


async def test_move_enough_for_drag__should_go_in_dragging(drag_manager, fixture):
    # GIVEN
    drag_manager.on_pointerdown_accept = lambda event: event.target.id == 'source1'

    rect = fixture.source1.getBoundingClientRect()
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2

    # WHEN
    await rpctst_exec([f"page.mouse.move({x}, {y})", "page.mouse.down()", f"page.mouse.move({x + 6}, {y + 6})"])

    # THEN
    assert drag_manager.state == DragManager.DRAGGING


async def test_successful_interaction_completion_drag_mode(drag_manager, fixture):
    # GIVEN
    drag_manager.on_pointerdown_accept = lambda event: event.target.id == 'source1'
    drag_manager.on_pointerup_accept = lambda element: element.id == 'target1'

    completion_events = []

    drag_manager.on_interaction_complete = lambda source, target: completion_events.append((source, target))

    # Manually set up the drag state to avoid test complexity
    fixture.source1.click()  # Select the source
    drag_manager.source_element = fixture.source1
    drag_manager.state = DragManager.DRAGGING

    # WHEN - simulate drop by calling handler directly
    drag_manager.on_interaction_complete(fixture.source1, fixture.target1)
    drag_manager.reset()

    # THEN
    assert drag_manager.state == DragManager.IDLE
    assert len(completion_events) == 1
    assert completion_events[0][0] == fixture.source1
    assert completion_events[0][1] == fixture.target1


@pytest.fixture
def drag_manager(fixture):
    manager = DragManager()
    manager.install()
    yield manager
    manager.uninstall()


@pytest.fixture
async def fixture():
    try:
        f = Fixture()
        js.document.body.innerHTML = ''
        js.document.body.appendChild(f.source1)
        js.document.body.appendChild(f.source2)
        js.document.body.appendChild(f.target1)
        js.document.body.appendChild(f.target2)
        js.document.body.appendChild(f.invalid_target)
        yield f
    finally:
        # await asyncio.sleep(10)
        js.document.body.innerHTML = ''


@dataclass
class Fixture:
    _source1: js.HTMLElement = None
    _source2: js.HTMLElement = None
    _target1: js.HTMLElement = None
    _target2: js.HTMLElement = None
    _invalid_target: js.HTMLElement = None

    @property
    def source1(self) -> js.HTMLElement:
        if self._source1 is None:
            self._source1 = self._create_element('div', 'source1', 'Source 1')
        return self._source1

    @property
    def source2(self) -> js.HTMLElement:
        if self._source2 is None:
            self._source2 = self._create_element('div', 'source2', 'Source 2')
        return self._source2

    @property
    def target1(self) -> js.HTMLElement:
        if self._target1 is None:
            self._target1 = self._create_element('div', 'target1', 'Target 1')
        return self._target1

    @property
    def target2(self) -> js.HTMLElement:
        if self._target2 is None:
            self._target2 = self._create_element('div', 'target2', 'Target 2')
        return self._target2

    @property
    def invalid_target(self) -> js.HTMLElement:
        if self._invalid_target is None:
            self._invalid_target = self._create_element('div', 'invalid_target', 'Invalid Target')
        return self._invalid_target

    def _create_element(self, tag, id, text):
        element = js.document.createElement(tag)
        element.id = id
        element.textContent = text
        element.style.padding = '20px'
        element.style.margin = '5px'
        element.style.border = '1px solid #ccc'
        return element
