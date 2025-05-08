from dataclasses import dataclass
from typing import Protocol


class RectReadOnly(Protocol):
    x: float
    y: float
    width: float
    height: float
    top: float
    right: float
    bottom: float
    left: float

    def toJSON(self) -> object: ...


@dataclass(frozen=True)
class RectReadOnlyDc(RectReadOnly):
    x: float
    y: float
    width: float
    height: float

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


def main() -> None:
    x = RectReadOnlyDc(x=0.0, y=0.0, width=1.0, height=1.0)
    print(x)
