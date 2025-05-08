from typing import Protocol


class RectReadOnly(Protocol):
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


class RectReadOnlyDc(RectReadOnly):

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
