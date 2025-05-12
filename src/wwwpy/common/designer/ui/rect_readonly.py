from typing import Protocol


class RectReadOnly(Protocol):
    """This is intended to be used in common to handle js.DOMRectReadOnly"""
    x: float
    y: float
    width: float
    height: float
    top: float
    right: float
    bottom: float
    left: float

    def toJSON(self) -> object: ...


def rect_xy_center(rect: RectReadOnly) -> tuple[float, float]:
    """Get the center x and y coordinates of the given rect."""
    x = rect.x + rect.width / 2
    y = rect.y + rect.height / 2
    return x, y


def rect_to_py(rect: RectReadOnly) -> RectReadOnly:
    from . import rect_readonly_py
    return rect_readonly_py.RectReadOnlyPy(rect)
