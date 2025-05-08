from typing import Protocol, overload, Union


class PyRectReadOnly(Protocol):
    """This is intended to be used in common to handle js.DOMRectReadOnly"""

    @property
    def x(self) -> float: ...

    @property
    def y(self) -> float: ...

    @property
    def width(self) -> float: ...

    @property
    def height(self) -> float: ...

    @property
    def left(self) -> float: ...

    @property
    def top(self) -> float: ...

    @property
    def right(self) -> float: ...

    @property
    def bottom(self) -> float: ...

    def toJSON(self) -> object: ...


class RectReadOnly(PyRectReadOnly):
    @overload
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        ...

    @overload
    def __init__(self, rect: PyRectReadOnly) -> None:
        ...

    def __init__(
            self,
            x: Union[float, PyRectReadOnly],
            y: float = None,
            width: float = None,
            height: float = None
    ) -> None:
        # duck‐type the “rect” overload
        if hasattr(x, "x") and hasattr(x, "y") and hasattr(x, "width") and hasattr(x, "height"):
            rect = x  # type: PyRectReadOnly
            self._x = rect.x
            self._y = rect.y
            self._width = rect.width
            self._height = rect.height
        else:
            # x,y,width,height overload
            self._x = x  # type: ignore
            self._y = y  # type: ignore
            self._width = width  # type: ignore
            self._height = height  # type: ignore

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def toJSON(self) -> object:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

