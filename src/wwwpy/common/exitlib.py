import sys
import weakref


class _Obj:
    pass


def on_exit(callback):
    frame = sys._getframe(1)
    obj = _Obj()
    frame.f_locals[obj] = obj
    weakref.finalize(obj, callback)
