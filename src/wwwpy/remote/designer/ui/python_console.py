import inspect
from dataclasses import dataclass

import wwwpy.remote.component as wpc
import js  # used in globals
from js import pyodide, document, console, window

import logging

from wwwpy.common import state

logger = logging.getLogger(__name__)


@dataclass
class State:
    python_code: str = ''


class PythonConsoleComponent(wpc.Component, tag_name='component-1'):
    _ta_python_code: js.HTMLTextAreaElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div>Run Python code:</div>
<textarea data-name="_ta_python_code" placeholder="Press CTRL-Enter to run code" rows="10" wrap="off" 
style="width: 95%;"></textarea>
"""
        self._state = state._restore(State)
        self._ta_python_code.value = self._state.python_code

    async def _ta_python_code__keydown(self, event):
        if event.ctrlKey and event.key == 'Enter':
            await js.pyodide.runPythonAsync(
                self._ta_python_code.value,
                globals=globals()
            )

    async def _ta_python_code__input(self, event):
        self._state.python_code = self._ta_python_code.value
