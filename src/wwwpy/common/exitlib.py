import sys
import weakref
from typing import Callable


class _Obj:
    pass


def on_exit(callback: Callable[[], None]) -> None:
    frame = sys._getframe(1)
    obj = _Obj()
    frame.f_locals[obj] = obj
    weakref.finalize(obj, callback)
