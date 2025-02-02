from wwwpy.common.databind.databind import TargetAdapter
import js

from pyodide.ffi import create_proxy

from wwwpy.common.property_monitor import PropertyChanged

# rename to HTMLInputTargetAdapter or HTMLInputTarget
class InputTargetAdapter(TargetAdapter):
    def __init__(self, inp: js.HTMLInputElement):
        super().__init__()
        self.input = inp
        self.input.addEventListener('input', create_proxy(self._new_input_event))

    def set_target_value(self, value):
        self.input.value = value

    def get_target_value(self):
        return self.input.value

    def _new_input_event(self, event):
        self.monitor_object.notify([PropertyChanged(self, '', None, self.input.value)])
