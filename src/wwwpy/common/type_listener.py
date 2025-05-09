from __future__ import annotations

from typing import TypeVar, Generic, Callable

T = TypeVar('T')


class TypeListeners(Generic[T], list[Callable[[T], None]]):
    def __init__(self, event_type: type[T] | None) -> None:
        super().__init__()
        self.event_type = event_type

    def add(self, handler: Callable[[T], None]) -> None:
        self.append(handler)

    def remove(self, handler: Callable[[T], None]) -> None:
        super().remove(handler)

    def notify(self, event: T) -> None:
        if self.event_type and not isinstance(event, self.event_type):
            raise TypeError(f'Handler expects {self.event_type}')
        for h in list(self):
            h(event)


class DictListeners:
    def __init__(self):
        self._listeners: dict[type, TypeListeners] = {}
        self.catch_all = TypeListeners(None)

    def on(self, event_type: type[T]) -> TypeListeners[T]:
        lst = self._listeners.get(event_type)
        if lst is None:
            lst = TypeListeners(event_type)
            self._listeners[event_type] = lst
        return lst

    def notify(self, ev: T) -> None:
        listeners = self._listeners.get(type(ev), None)
        if listeners:
            listeners.notify(ev)
        self.catch_all.notify(ev)
