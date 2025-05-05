from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar, Generic

T = TypeVar('T')


@dataclass
class ExtensionPointList(Generic[T]):
    extensions: list[T] = field(default_factory=list)
