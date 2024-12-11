from dataclasses import dataclass

from wwwpy.common import collectionlib as cl


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
