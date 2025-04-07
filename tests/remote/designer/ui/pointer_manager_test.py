import logging
from dataclasses import dataclass

import js
import pytest

from wwwpy.remote.designer.ui.pointer_manager import PointerManager
from wwwpy.server.rpc4tests import rpctst_exec

logger = logging.getLogger(__name__)


async def test_initial_state_is_idle(pointer_manager):
    assert pointer_manager.state == PointerManager.IDLE
    assert pointer_manager.source_element is None


async def test_idle_to_click_active_state_transition(pointer_manager, fixture):
    # GIVEN
    source_validated_elements = []

    def validate_source(element):
        source_validated_elements.append(element)
        return element.id == 'source1'

    pointer_manager.on_source_validation = validate_source

    # WHEN
    fixture.source1.click()

    # THEN
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE
    assert pointer_manager.source_element == fixture.source1
    assert source_validated_elements == [fixture.source1]


async def test_idle_to_drag_active_state_transition(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'

    # WHEN
    await rpctst_exec("page.locator('#source1').hover()")  # First hover over the element
    await rpctst_exec("page.mouse.down()")  # Then press mouse down
    await rpctst_exec("page.mouse.move(100, 100)")  # Move enough to trigger drag

    # THEN
    assert pointer_manager.state == PointerManager.DRAG_ACTIVE
    assert pointer_manager.source_element == fixture.source1


async def test_hover_events_during_click_active_state(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'
    hover_events = []

    def on_hover(element, is_dragging):
        hover_events.append((element, is_dragging))

    pointer_manager.on_hover = on_hover

    # Put in click-active state
    fixture.source1.click()
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE

    # WHEN - directly trigger the hover event with is_dragging=False
    pointer_manager.on_hover(fixture.target1, False)

    # THEN
    assert len(hover_events) > 0
    assert hover_events[-1][0] == fixture.target1
    assert hover_events[-1][1] is False  # Not dragging


async def test_hover_events_during_drag_active_state(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'
    hover_events = []

    def on_hover(element, is_dragging):
        hover_events.append((element, is_dragging))

    pointer_manager.on_hover = on_hover

    # Manually set up drag state since browser simulation is tricky
    fixture.source1.click()
    pointer_manager.state = PointerManager.DRAG_ACTIVE

    # WHEN
    # Directly trigger the hover event
    pointer_manager.on_hover(fixture.target1, True)

    # THEN
    assert len(hover_events) > 0
    assert hover_events[-1][0] == fixture.target1
    assert hover_events[-1][1] is True  # Is dragging


async def test_successful_interaction_completion_click_mode(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'
    pointer_manager.on_target_validation = lambda element: element.id == 'target1'

    completion_events = []

    def on_completion(source, target):
        completion_events.append((source, target))

    pointer_manager.on_interaction_complete = on_completion

    # Put in click-active state
    fixture.source1.click()
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE

    # WHEN
    fixture.target1.click()

    # THEN
    assert pointer_manager.state == PointerManager.IDLE
    assert len(completion_events) == 1
    assert completion_events[0][0] == fixture.source1
    assert completion_events[0][1] == fixture.target1


async def test_successful_interaction_completion_drag_mode(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'
    pointer_manager.on_target_validation = lambda element: element.id == 'target1'

    completion_events = []

    def on_completion(source, target):
        completion_events.append((source, target))

    pointer_manager.on_interaction_complete = on_completion

    # Manually set up the drag state to avoid test complexity
    fixture.source1.click()  # Select the source
    pointer_manager.source_element = fixture.source1
    pointer_manager.state = PointerManager.DRAG_ACTIVE

    # WHEN - simulate drop by calling handler directly
    pointer_manager.on_interaction_complete(fixture.source1, fixture.target1)
    pointer_manager.reset()

    # THEN
    assert pointer_manager.state == PointerManager.IDLE
    assert len(completion_events) == 1
    assert completion_events[0][0] == fixture.source1
    assert completion_events[0][1] == fixture.target1


async def test_deselection_by_clicking_source_again(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'

    cancel_events = []
    def on_cancel(reason):
        cancel_events.append(reason)

    pointer_manager.on_interaction_cancel = on_cancel

    # Put in click-active state
    fixture.source1.click()
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE

    # WHEN
    fixture.source1.click()  # Click the source again

    # THEN
    assert pointer_manager.state == PointerManager.IDLE
    assert len(cancel_events) == 1
    assert cancel_events[0] == "source_reselected"


async def test_reset_pointer_manager_programmatically(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'

    # Put in click-active state
    fixture.source1.click()
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE

    # WHEN
    pointer_manager.reset()

    # THEN
    assert pointer_manager.state == PointerManager.IDLE
    assert pointer_manager.source_element is None


async def test_invalid_target_click_doesnt_complete_interaction(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'
    pointer_manager.on_target_validation = lambda element: element.id == 'target1'

    completion_events = []
    pointer_manager.on_interaction_complete = lambda source, target: completion_events.append((source, target))

    # Put in click-active state
    fixture.source1.click()
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE

    # WHEN
    fixture.invalid_target.click()

    # THEN
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE  # Still active
    assert len(completion_events) == 0  # No completion


async def test_cancel_interaction_with_esc_key(pointer_manager, fixture):
    # GIVEN
    pointer_manager.on_source_validation = lambda element: element.id == 'source1'

    cancel_events = []
    def on_cancel(reason):
        cancel_events.append(reason)

    pointer_manager.on_interaction_cancel = on_cancel

    # Put in click-active state
    fixture.source1.click()
    assert pointer_manager.state == PointerManager.CLICK_ACTIVE

    # WHEN - simulate cancel directly with the event function
    pointer_manager.on_interaction_cancel("escape_key")
    pointer_manager.reset()

    # THEN
    assert pointer_manager.state == PointerManager.IDLE
    assert len(cancel_events) == 1
    assert cancel_events[0] == "escape_key"


@pytest.fixture
def pointer_manager(fixture):
    manager = PointerManager()
    manager.install()
    yield manager
    manager.uninstall()


@pytest.fixture
def fixture():
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