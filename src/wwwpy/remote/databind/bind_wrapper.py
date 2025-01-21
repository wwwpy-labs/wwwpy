from wwwpy.common.databind.databind import TargetAdapter
import js

from pyodide.ffi import create_proxy


class InputTargetAdapter(TargetAdapter):
    def __init__(self, inp: js.HTMLInputElement):
        super().__init__()
        self.inp = inp
        self.inp.addEventListener('input', create_proxy(self._new_input_event))

    def set_target_value(self, value):
        self.inp.value = value

    def get_target_value(self):
        return self.inp.value

    def _new_input_event(self, event):
        # lambda event: setattr(car1, 'color', tag1.value)
        for l in self.listeners:
            l(event)
