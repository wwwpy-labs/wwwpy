from dataclasses import dataclass

from wwwpy.common import collectionlib as cl
from wwwpy.common.collectionlib import ObservableList


@dataclass
class Item:
    name: str
    color: str


class MyListMap(cl.ListMap[Item]):
    def _key(self, item: Item) -> str:
        return item.name


def test_add_item():
    # GIVEN
    target = MyListMap()

    # WHEN
    target.append(Item('apple', 'red'))

    # THEN
    assert len(target) == 1
    assert target.get('apple').color == 'red'


def test_insert_item():
    # GIVEN
    target = MyListMap()

    # WHEN
    target.insert(0, Item('apple', 'red'))

    # THEN
    assert len(target) == 1
    assert target.get('apple').color == 'red'


def test_extend_items():
    # GIVEN
    target = MyListMap()

    # WHEN
    target.extend([Item('apple', 'red'), Item('banana', 'yellow')])

    # THEN
    assert len(target) == 2
    assert target.get('apple').color == 'red'
    assert target.get('banana').color == 'yellow'


def test_items_in_constructor():
    # GIVEN
    target = MyListMap([Item('apple', 'red'), Item('banana', 'yellow')])

    # THEN
    assert len(target) == 2
    assert target.get('apple').color == 'red'
    assert target.get('banana').color == 'yellow'
    assert target.get('missing') is None


def test_keyfunc_in_constructor():
    # GIVEN
    target = cl.ListMap([Item('apple', 'red'), Item('banana', 'yellow')], key_func=lambda x: x.color)

    # THEN
    assert len(target) == 2
    assert target.get('red').name == 'apple'
    assert target.get('yellow').name == 'banana'


def test_equality_with_list():
    # GIVEN
    target = cl.ListMap(['a', 'b', 'c'])

    # THEN
    assert target == ['a', 'b', 'c']


########### ObservableList test

class ObservableListFake(ObservableList):
    def __init__(self, *args):
        super().__init__(*args)
        self.added = []
        self.removed = []

    def _item_added(self, item, index):
        self.added.append((item, index))

    def _item_removed(self, item, index):
        self.removed.append((item, index))


class TestObservableList:
    def test_initialization_empty(self):
        ol = ObservableListFake()
        assert ol == []
        assert ol.added == []
        assert ol.removed == []

    def test_initialization_with_data(self):
        ol = ObservableListFake([1, 2, 3])
        assert ol == [1, 2, 3]
        assert ol.added == []
        assert ol.removed == []

    def test_append(self):
        ol = ObservableListFake()
        ol.append('a')
        assert ol == ['a']
        assert ol.added == [('a', 0)]
        assert ol.removed == []

    def test_extend(self):
        ol = ObservableListFake()
        ol.extend(['a', 'b'])
        assert ol == ['a', 'b']
        assert ol.added == [('a', 0), ('b', 1)]

    def test_insert(self):
        ol = ObservableListFake([1, 3])
        ol.insert(1, 2)
        assert ol == [1, 2, 3]
        assert ol.added == [(2, 1)]

    def test_insert_at_beginning(self):
        ol = ObservableListFake([2, 3])
        ol.insert(0, 1)
        assert ol == [1, 2, 3]
        assert ol.added == [(1, 0)]

    def test_remove(self):
        ol = ObservableListFake([1, 2, 3])
        ol.remove(2)
        assert ol == [1, 3]
        assert ol.removed == [(2, 1)]

    def test_pop(self):
        ol = ObservableListFake([1, 2, 3])
        item = ol.pop()
        assert item == 3
        assert ol == [1, 2]
        assert ol.removed == [(3, 2)]

    def test_pop_with_index(self):
        ol = ObservableListFake([1, 2, 3])
        result = ol.pop(0)
        assert result == 1
        assert ol == [2, 3]
        assert ol.removed == [(1, 0)]

    def test_clear(self):
        ol = ObservableListFake([1, 2])
        ol.clear()
        assert ol == []
        assert ol.removed == [(1, 0), (2, 1)]

    def test_setitem_single(self):
        ol = ObservableListFake([1, 2, 3])
        ol[1] = 'x'
        assert ol == [1, 'x', 3]
        assert ol.removed == [(2, 1)]
        assert ol.added == [('x', 1)]

    def test_setitem_slice(self):
        ol = ObservableListFake([1, 2, 3, 4])
        ol[1:3] = ['a', 'b']
        assert ol == [1, 'a', 'b', 4]
        assert ('a', 1) in ol.added and ('b', 2) in ol.added
        assert (2, 1) in ol.removed and (3, 2) in ol.removed

    def test_delitem_single(self):
        ol = ObservableListFake([1, 2, 3])
        del ol[1]
        assert ol == [1, 3]
        assert ol.removed == [(2, 1)]

    def test_delitem_slice(self):
        ol = ObservableListFake([1, 2, 3, 4])
        del ol[1:3]
        assert ol == [1, 4]
        assert (2, 1) in ol.removed and (3, 2) in ol.removed

    def test_iadd(self):
        ol = ObservableListFake([1])
        ol += [2, 3]
        assert ol == [1, 2, 3]
        assert ol.added[-2:] == [(2, 1), (3, 2)]

    def test_imul(self):
        ol = ObservableListFake([1, 2])
        ol *= 3
        assert ol == [1, 2, 1, 2, 1, 2]
        assert ol.added == [(1, 2), (2, 3), (1, 4), (2, 5)]

    def test_add(self):
        ol = ObservableListFake([1])
        new = ol + [2]
        assert isinstance(new, ObservableListFake)
        assert new == [1, 2]
        assert new.added == [(2, 1)]

    def test_complex_operations_sequence(self):
        ol = ObservableListFake()
        ol.append(1)
        ol.extend([2, 3])
        ol.insert(1, 99)
        ol[0] = 100
        assert ol == [100, 99, 2, 3]
        expected_added = [(1, 0), (2, 1), (3, 2), (99, 1), (100, 0)]
        expected_removed = [(1, 0)]
        assert ol.added == expected_added
        assert ol.removed == expected_removed

    def test_edge_case_empty_extend(self):
        ol = ObservableListFake([1, 2])
        ol.extend([])
        assert ol == [1, 2]
        assert ol.added == []
        assert ol.removed == []

    def test_edge_case_empty_slice_assignment(self):
        ol = ObservableListFake([1, 2, 3])
        ol[1:1] = [99]
        assert ol == [1, 99, 2, 3]
        assert ol.added == [(99, 1)]
        assert ol.removed == []

    def test_negative_indexing(self):
        ol = ObservableListFake([1, 2, 3])
        ol[-1] = 99
        assert ol == [1, 2, 99]
        assert ol.added == [(99, 2)]
        assert ol.removed == [(3, 2)]
