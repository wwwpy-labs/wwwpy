from __future__ import annotations

import logging

from wwwpy.common.type_listener import TypeListeners
from wwwpy.remote.designer.ui.design_aware import find_intent_da
from wwwpy.remote.designer.ui.intent import Intent, IntentChangedEvent
from wwwpy.remote.designer.ui.pointer_api import PointerApi, PointerDown, PointerMove, PointerUp

logger = logging.getLogger(__name__)


class IntentManager:

    def __init__(self) -> None:
        self._current_selection: Intent | None = None
        self._intent_changed_listeners = TypeListeners(IntentChangedEvent)
        self._ready_item: Intent | None = None

        self._pointer_api = PointerApi()
        self._pointer_api.on(PointerDown).add(self._on_pointer_down)
        self._pointer_api.on(PointerMove).add(self._on_pointer_move)
        self._pointer_api.on(PointerUp).add(self._on_pointer_up)

    def install(self) -> None:
        self._pointer_api.install()

    def uninstall(self) -> None:
        self._pointer_api.uninstall()

    @property
    def drag_state(self) -> str:
        return self._pointer_api.drag_state

    def on(self, event_type: type[IntentChangedEvent]) -> TypeListeners[IntentChangedEvent]:
        if event_type is not IntentChangedEvent:
            raise TypeError(f'IntentManager only supports {IntentChangedEvent}')
        return self._intent_changed_listeners

    def _toggle_selection(self, intent: Intent):
        if intent == self.current_selection:
            self.current_selection = None
        else:
            self.current_selection = intent

    def _on_pointer_down(self, event: PointerDown):
        intent = find_intent_da(event.js_event)
        logger.debug(f'_on_pointer_down {intent} state={self.drag_state}')
        if intent:
            self._ready_item = intent
            event.start_drag()
        else:
            se = self.current_selection
            if se is not None:
                if se.on_submit_js(event.js_event):
                    event.stop()
                    self.current_selection = None

    def _on_pointer_move(self, event: PointerMove):
        intent = find_intent_da(event.js_event)
        logger.debug(f'_on_pointer_move {intent} state={self.drag_state} '
                     f'ready_item={self._ready_item} drag_started={event.drag_started}')
        if event.drag_started and self._ready_item is not None:
            self.current_selection = self._ready_item
            self._ready_item = None

        if intent:
            return

        se = self.current_selection
        if se is not None:
            se.on_hover_js(event.js_event)

    def _on_pointer_up(self, event: PointerUp):
        intent = find_intent_da(event.js_event)
        logger.debug(f'_on_pointer_up {intent} state={self.drag_state} ready_item={self._ready_item}')

        if event.stopped: ...

        ready = self._ready_item
        self._ready_item = None

        if event.normal_click:
            if intent:
                if ready is not None:
                    self._toggle_selection(ready)
        elif event.drag_ended:
            if intent:
                return  # this return is not under test; when we pointerdown on an intent, and drag
                # (just enough) and release on the intent itself
            se = self.current_selection
            if se is not None:
                if se.on_submit_js(event.js_event):
                    self.current_selection = None

    @property
    def current_selection(self) -> Intent | None:
        return self._current_selection

    @current_selection.setter
    def current_selection(self, new: Intent | None) -> None:
        msg = ''
        if self._ready_item:
            msg += f' ri={self._ready_item}'

        old = self.current_selection
        if old == new:
            msg += f' (no change) old={old}'
            logger.debug(msg)
            return

        if old:
            old.selected = False
            old.on_deselected()
            msg += f' (deselecting {old})'

        self._current_selection = new
        msg += f' (selecting {None if new is None else new})'
        if new:
            new.selected = True
            new.on_selected()

        self._intent_changed_listeners.notify(IntentChangedEvent(old, new))

        logger.debug(msg)


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
