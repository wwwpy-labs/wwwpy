from __future__ import annotations

import logging

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js, dict_to_py
from wwwpy.remote.designer.ui.floater import Floater
from wwwpy.remote.designer.ui.floater_action_band import ActionBandFloater
from wwwpy.remote.designer.ui.floater_selection_indicator import SelectionIndicatorFloater
from wwwpy.remote.jslib import is_contained, AnimationFrameTracker

logger = logging.getLogger(__name__)


# logger.setLevel(logging.DEBUG)

# todo extract the logic of the animation frame tracker
class ElementSelector(wpc.Component, tag_name='element-selector'):
    selection_indicator: SelectionIndicatorFloater = wpc.element()
    action_band: ActionBandFloater = wpc.element()

    # _eventbus: EventBus = inject()

    def init_component(self):
        # Existing code remains the same
        self.element.attachShadow(dict_to_js({'mode': 'open'}))

        # language=html
        self.element.shadowRoot.innerHTML = """
        <selection-indicator-floater data-name="selection_indicator"></selection-indicator-floater>
        <action-band-floater data-name="action_band"></action-band-floater>
        """
        self._selected_element: js.HTMLElement | None = None
        self._last_position = None
        self._update_count = 0
        self._animation_frame_tracker = AnimationFrameTracker(self._on_animation_frame)

    def connectedCallback(self):
        has_py_comp = hasattr(self.element, '_python_component')
        logger.debug(f'has_py_comp: {has_py_comp}')

    def disconnectedCallback(self):
        self._animation_frame_tracker.stop()

    def is_selectable(self, element) -> bool:
        ok = not is_contained(element, self.element)
        return ok

    def set_selected_element(self, element):
        if element is not None and not self.is_selectable(element):
            raise ValueError(f'Element is not selectable `{dict_to_py(element)}`')

        if self._selected_element == element:
            return

        self._animation_frame_tracker.stop()
        self._selected_element = element
        self._last_position = None

        if element:
            self._animation_frame_tracker.start()
        else:
            self.selection_indicator.hide()
            self.action_band.hide()

    def get_selected_element(self):
        return self._selected_element

    def _on_animation_frame(self, timestamp):
        rect = self._selected_element.getBoundingClientRect()
        rect_tup = (rect.top, rect.left, rect.width, rect.height)
        if self._last_position == rect_tup:
            return

        skip_transition = self._last_position is not None

        self._update_count += 1
        logger.debug(f'update_highlight: {self._update_count} skip_transition: {skip_transition}')

        self.selection_indicator.transition = not skip_transition

        for x in [self.selection_indicator, self.action_band]:
            x: Floater
            x.set_reference_geometry(rect)

        self._last_position = rect_tup


