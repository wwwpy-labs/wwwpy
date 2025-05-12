from typing import overload, Union

from wwwpy.common.designer.ui.rect_readonly import RectReadOnly


class RectReadOnlyPy(RectReadOnly):
    @overload
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        ...

    @overload
    def __init__(self, rect: RectReadOnly) -> None:
        ...

    def __init__(
            self,
            x: Union[float, RectReadOnly],
            y: float = None,
            width: float = None,
            height: float = None
    ) -> None:
        # duck‐type the “rect” overload
        if hasattr(x, "x") and hasattr(x, "y") and hasattr(x, "width") and hasattr(x, "height"):
            rect = x  # type: RectReadOnly
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

    @property
    def xy_center(self) -> tuple[float, float]:
        """Get the center x and y coordinates of the rect."""
        return self.x + self.width / 2, self.y + self.height / 2

    def __repr__(self) -> str:
        return f"RectReadOnlyPy(x={self.x}, y={self.y}, width={self.width}, height={self.height})"
