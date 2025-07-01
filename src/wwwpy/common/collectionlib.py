from __future__ import annotations

from typing import Callable, TypeVar, Collection

T = TypeVar('T')
K = TypeVar('K')


class ListMap(list[T]):
    def __init__(self, args: Collection[T] = (), key_func: Callable[[T], K] = None):
        super().__init__(args)
        if key_func is not None:
            self._key = key_func
        self._map = {self._key(item): item for item in self}

    # __add__ = _modify_method(list.__add__, takes_list=True)
    # __iadd__ = _modify_method(list.__iadd__, takes_list=True)
    # __setitem__ = _modify_method(list.__setitem__, 1)
    def _key(self, item: T) -> K:
        return item

    def append(self, value: T):
        self._map[self._key(value)] = value
        super().append(value)

    def insert(self, index: int, value: T):
        self._map[self._key(value)] = value
        super().insert(index, value)

    def extend(self, values: Collection[T]):
        for value in values:
            self._map[self._key(value)] = value
        super().extend(values)

    def get(self, key: K) -> T | None:
        """Return the item with the given key or None if it does not exist."""
        return self._map.get(key)


from collections import UserList


class ObservableList(UserList):
    def _item_added(self, item, index):
        pass

    def _item_removed(self, item, index):
        pass

    def append(self, item):
        super().append(item)
        self._item_added(item, len(self.data) - 1)

    def extend(self, items):
        start = len(self.data)
        super().extend(items)
        for i, item in enumerate(items, start):
            self._item_added(item, i)

    def insert(self, index, item):
        super().insert(index, item)
        self._item_added(item, index)

    def remove(self, item):
        idx = self.data.index(item)
        super().remove(item)
        self._item_removed(item, idx)

    def pop(self, index=-1):
        idx = index if index >= 0 else len(self.data) + index
        item = super().pop(index)
        self._item_removed(item, idx)
        return item

    def clear(self):
        for i, item in enumerate(self.data):
            self._item_removed(item, i)
        super().clear()

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            old = self.data[index]
            super().__setitem__(index, value)
            for i, item in enumerate(value, index.start or 0):
                self._item_added(item, i)
            for i, item in enumerate(old, index.start or 0):
                self._item_removed(item, i)
        else:
            idx = index if index >= 0 else len(self.data) + index
            old = self.data[index]
            super().__setitem__(index, value)
            self._item_removed(old, idx)
            self._item_added(value, idx)

    def __delitem__(self, index):
        if isinstance(index, slice):
            for i, item in enumerate(self.data[index], index.start or 0):
                self._item_removed(item, i)
        else:
            idx = index if index >= 0 else len(self.data) + index
            item = self.data[index]
            self._item_removed(item, idx)
        super().__delitem__(index)

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __imul__(self, n):
        original = list(self.data)
        for _ in range(n - 1):
            self.extend(original)
        return self

    def __add__(self, other):
        new = type(self)(self.data + list(other))
        for i, item in enumerate(other, len(self.data)):
            new._item_added(item, i)
        return new
