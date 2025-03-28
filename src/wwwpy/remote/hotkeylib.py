from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional, Dict, Union, Awaitable

import js
from js import console, window, EventTarget, KeyboardEvent
from pyodide.ffi import create_proxy, to_js

logger = logging.getLogger(__name__)

HotkeyHandler = Union[Callable[['KeyboardEvent'], Optional[bool]], Callable[['KeyboardEvent'], Awaitable[None]]]


class Hotkey:
    def __init__(self, element: EventTarget):
        self.element = element
        self.handlers: Dict[str, HotkeyHandler] = dict()
        self.debug = False
        self._proxy = create_proxy(self._detect_hotkey)
        self.install()

    def install(self):
        self.element.addEventListener('keydown', self._proxy, False)

    def uninstall(self):
        self.element.removeEventListener('keydown', self._proxy, False)

    # todo this should be called 'set'
    def add(self, hotkey: str, handler: HotkeyHandler) -> 'Hotkey':
        """
        Registers a hotkey with its corresponding handler.

        Adds a key-handler pair to the handlers dictionary, associating the hotkey with
        the given handler function or callable.

        Parameters
        ----------
        hotkey : str
            The key combination that will trigger the handler. Examples: 'CTRL-S', 'Escape', 'META-Backspace'
            , 'CTRL-SHIFT-ALT-META-F1', this last example serves to know the order of the modifiers.
        handler : HotkeyHandler
            A function or callable that will be called when the hotkey is pressed.
        """
        self.handlers[hotkey] = handler
        return self

    @classmethod
    def keyboard_event(cls, e):
        return js.eval('(e) => e instanceof KeyboardEvent ')(e)

    def _detect_hotkey(self, e):
        if not self.keyboard_event(e):
            return
        key = ''
        if e.ctrlKey: key += 'CTRL-'
        if e.shiftKey: key += 'SHIFT-'
        if e.altKey: key += 'ALT-'
        if e.metaKey: key += 'META-'

        upc: str = e.key
        if len(upc) == 1: upc = upc.upper()

        key += upc
        if self.debug:
            console.log(key, to_js(e))
            logger.debug(f'key = `{key}`')

        handle = self.handlers.get(key, None)
        if handle is None:
            return
        e.hotkey = key  # add the hotkey attribute to the event
        if asyncio.iscoroutinefunction(handle):
            e.preventDefault()
            e.stopPropagation()
            asyncio.create_task(handle(e))
            return

        res = handle(e)
        if not res:
            return

        console.log(f'prevent default for {key}')
        e.preventDefault()
        e.stopPropagation()
