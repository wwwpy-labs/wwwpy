from __future__ import annotations

import logging

import js

from wwwpy.common.type_listener import TypeListeners, DictListeners
from wwwpy.remote.designer.ui.action import PMEvent, TPE, SubmitEvent, HoverEvent, Action, ActionChangedEvent
from wwwpy.remote.designer.ui.action_aware import IdentifyActionEvent, ActionAware
from wwwpy.remote.designer.ui.pointer_api import PointerApi, PointerDown, PointerMove, PointerUp
from wwwpy.remote.jslib import get_deepest_element

logger = logging.getLogger(__name__)


class ActionManager:

    def __init__(self) -> None:
        self._selected_action: Action | None = None
        self._listeners = DictListeners()
        self._ready_item: Action | None = None

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

    def on(self, event_type: type[TPE]) -> TypeListeners[TPE]:
        return self._listeners.on(event_type)

    def _notify(self, ev: PMEvent) -> None:
        self._listeners.notify(ev)

    def _toggle_selection(self, action: Action):
        if action == self.selected_action:
            self.selected_action = None
        else:
            self.selected_action = action

    def _on_pointer_down(self, event: PointerDown):
        action = _request_identification(event.js_event)
        logger.debug(f'_on_pointer_down {action} state={self.drag_state}')
        if action:
            self._ready_item = action
            event.start_drag()
        else:
            se = self.selected_action
            ae = SubmitEvent(event.js_event)
            self._notify(ae)
            if se is not None:
                event.stop()
                se.on_execute(ae)
                if ae.accepted:
                    self.selected_action = None

    def _on_pointer_move(self, event: PointerMove):
        action = _request_identification(event.js_event)
        logger.debug(f'_on_pointer_move {action} state={self.drag_state} '
                     f'ready_item={self._ready_item} drag_started={event.drag_started}')
        if event.drag_started and self._ready_item is not None:
            self.selected_action = self._ready_item
            self._ready_item = None

        if action:
            return

        hover_event = HoverEvent(event.js_event)
        self._notify(hover_event)
        se = self.selected_action
        if se is not None:
            se.on_hover(hover_event)

    def _on_pointer_up(self, event: PointerUp):
        action = _request_identification(event.js_event)
        logger.debug(f'_on_pointer_up {action} state={self.drag_state} ready_item={self._ready_item}')

        if event.stopped: ...

        ready = self._ready_item
        self._ready_item = None

        if event.normal_click:
            if action:
                if ready is not None:
                    self._toggle_selection(ready)
        elif event.drag_ended:
            if action:
                return  # this return is not under test; when we pointerdown on an action, and drag
                # (just enough) and release on the action itself
            ae = SubmitEvent(event.js_event)
            self._notify(ae)
            se = self.selected_action
            if se is not None:
                se.on_execute(ae)
                if ae.accepted:
                    self.selected_action = None

    @property
    def selected_action(self) -> Action | None:
        return self._selected_action

    @selected_action.setter
    def selected_action(self, new: Action | None) -> None:
        msg = ''
        if self._ready_item:
            msg += f' ri={self._ready_item}'

        old = self.selected_action
        if old == new:
            msg += f' (no change) old={old}'
            logger.debug(msg)
            return

        if old:
            old.selected = False
            old.on_deselect()
            msg += f' (deselecting {old})'

        self._selected_action = new
        msg += f' (selecting {None if new is None else new})'
        if new:
            new.selected = True
            new.on_selected()
        self._notify(ActionChangedEvent(old, new))

        logger.debug(msg)


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)


def _request_identification(js_event: js.PointerEvent) -> Action | None:
    target = get_deepest_element(js_event.clientX, js_event.clientY)
    if target is None:  # happens, e.g., when the mouse is moved on the scrollbar; no test for this (yet)
        return None
    ie = IdentifyActionEvent(js_event, target)
    for extension in ActionAware.EP_LIST.extensions:
        action = extension.find_action(ie)
        if action:
            return action
    return None
