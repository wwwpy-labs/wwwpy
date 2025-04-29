from __future__ import annotations

import js

from wwwpy.remote.component import get_component
from wwwpy.remote.designer.ui.pointer_manager import PointerManager, IdentifyEvent, TPE, TypeListeners
from wwwpy.remote.jslib import get_deepest_element


class ActionItem:
    key: any
    """Unique object to identify the item in the palette."""

    label: str
    """Label to be displayed in the palette item."""

    selected: bool
    """True if the item is selected, False otherwise."""


class ActionManager:
    """A class to manage interaction and events to handle, drag & drop, element selection, move element."""

    def __init__(self):
        self.pointer_manager: PointerManager[ActionItem] = PointerManager()
        self.pointer_manager.listeners_for(IdentifyEvent).add(self._identify_event)
        # self._selected_action: ActionItem | None = None
        # self.on_events: PaletteEventHandler = lambda ev: None
        # self._listeners = dict[type[_PE], list[PaletteEventHandler]]()
        # self._drag_fsm = DragFsm()
        # self._ready_item = None
        # self._stopped = False
        # self._stop_next_click = False  # new flag to also suppress the subsequent click

    def _identify_event(self, event: IdentifyEvent):
        event.action = _find_palette_item(event.js_event)
        event.identified_as = 'action' if event.action else 'canvas'

    def install(self):
        # eventlib.add_event_listeners(self)
        self.pointer_manager.install()

    def uninstall(self):
        # eventlib.remove_event_listeners(self)
        self.pointer_manager.uninstall()

    @property
    def drag_state(self):
        return self.pointer_manager.drag_state

    # @handler_options(capture=True)
    # def _js_window__click(self, event):
    #     if not self._in_palette(event) and self._stop_next_click:
    #         self._stop(event)
    #     self._stop_next_click = False

    # @handler_options(capture=True)
    # def _js_window__pointerdown(self, event):
    #     palette_item = _find_palette_item(event)
    #     logger.debug(
    #         f'_js_window__pointerdown {self._fsm_state()} pi={_pretty(palette_item)} event={dict_to_py(event)}')
    #     if palette_item:
    #         self._ready_item = palette_item
    #         self._drag_fsm.pointerdown_accepted(event)
    #     else:
    #         gesture_event = DeselectEvent(event)
    #         self._notify(gesture_event)
    #         if gesture_event.accepted:
    #             if self.selected_action is not None:
    #                 self._stop(event)
    #                 self._stopped = True
    #                 self._stop_next_click = True  # flag the next click for suppression
    #             self.selected_action = None

    # def _js_window__pointermove(self, event):
    #     palette_item = _find_palette_item(event)
    #     dragging = self._drag_fsm.transitioned_to_dragging(event)
    #
    #     msg = f'_js_window__pointermove {self._fsm_state()} pi={_pretty(palette_item)} ri={_pretty(self._ready_item)} dragging={dragging} event={dict_to_py(event)}'
    #     logger.debug(msg)
    #
    #     if dragging:
    #         self.selected_action = self._ready_item
    #         self._ready_item = None
    #
    #     if palette_item:
    #         return
    #
    #     hover_event = HoverEvent(event)
    #     self._notify(hover_event)
    #     logger.debug(f'_js_window__pointermove hover_event: {hover_event}')

    # @handler_options(capture=True)
    # def _js_window__pointerup(self, event):
    #     logger.debug(f'_js_window__pointerup _stopped={self._stopped} event={dict_to_py(event)}')
    #     if self._stopped:
    #         self._stop(event)
    #         self._stopped = False
    #     self._ready_item = None
    #     if self._drag_fsm.state == DragFsm.READY:
    #         # If the drag was not accepted, we can assume it was a click
    #         palette_item = _find_palette_item(event)
    #         if palette_item:
    #             self._toggle_selection(palette_item)
    #     if self._drag_fsm.state == DragFsm.DRAGGING:
    #         gesture_event = DeselectEvent(event)
    #         self._notify(gesture_event)
    #         if gesture_event.accepted:
    #             self.selected_action = None
    #     self._drag_fsm.pointerup(event)

    # def _fsm_state(self) -> str:
    #     return f'fsm={self._drag_fsm.state}'

    # def _notify(self, event: _PE):
    #     """Notify all listeners of the event."""
    #     listeners = self.listeners_for(type(event))
    #     if listeners:
    #         listeners.notify(event)
    #     self.on_events(event)

    def listeners_for(self, event_type: type[TPE]) -> TypeListeners[TPE]:
        return self.pointer_manager.listeners_for(event_type)
        # res = self._listeners.get(event_type)
        # if res is None:
        #     res = TypeListeners(event_type)
        #     self._listeners[event_type] = res
        # return res

    # def _in_palette(self, event: js.Event) -> bool:
    #     target = _element_from_js_event(event)
    #     return target.closest(PaletteComponent.component_metadata.tag_name) is not None
    # ptag = PaletteComponent.component_metadata.tag_name
    # logger.debug(f'target.tagName={target.tagName} ptag={ptag}')
    # is_pal = element.tagName.casefold() == ptag.casefold()
    # logger.debug(f'is in palette: {is_pal}')
    # return is_pal

    # def _stop(self, event):
    #     event.stopPropagation()
    #     event.preventDefault()
    #     event.stopImmediatePropagation()

    # def _in_canvas(self, event: js.Event) -> bool:
    #     return not self._in_palette(event)

    @property
    def selected_action(self) -> ActionItem | None:
        return self.pointer_manager.selected_action

    @selected_action.setter
    def selected_action(self, value: ActionItem | None):
        self.selected_action = value

    # def _toggle_selection(self, item: ActionItem):
    #     logger.debug(f'Item clicked: {item}')
    #     if item == self.selected_action:
    #         self.selected_action = None
    #         return
    #
    #     self.selected_action = item


def _find_palette_item(event: js.Event) -> PaletteItem | None:
    target = _element_from_js_event(event)
    if target is None:  # tests missing. It looks like it happens when the mouse exit the viewport or moves on the scrollbar
        return None
    # logger.debug(f'_find_palette_item target={_pretty(target)}')
    import wwwpy.remote.designer.ui.palette as palette
    res = target.closest(palette.PaletteItemComponent.component_metadata.tag_name)
    if res:
        return get_component(res)
    return None


def _element_from_js_event(event: js.Event) -> js.Element | None:
    return get_deepest_element(event.clientX, event.clientY)
