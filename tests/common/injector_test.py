from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Generic

import pytest

from wwwpy.common import injector
from wwwpy.common.injector import inject


class Pet: ...


class Dog(Pet): ...


class Cat(Pet): ...


_T = TypeVar('_T')


class SomeClass(Generic[_T]): ...


def test_register_get(fixture):
    pet = Pet()
    injector.register(pet)

    assert pet is injector.get(Pet)


def test_inject_descriptor(fixture):
    class A:
        pet: Pet = inject()

    p = Pet()
    injector.register(p)

    assert A().pet is p


def test_inject_descriptor_set__should_raise(fixture):
    class A:
        pet: Pet = inject()

    p = Pet()
    injector.register(p)

    pytest.raises(injector.InjectorError, setattr, A(), 'pet', Dog())


def test_polymorphism(fixture):
    dog = Dog()

    injector.register(dog, bind=Pet)

    assert injector.get(Pet) is dog


def test_register_multiple_should_throw(fixture):
    dog = Dog()
    injector.register(dog, bind=Pet)

    pytest.raises(injector.InjectorError, injector.register, dog, bind=Pet)


def test_unregister(fixture):
    dog = Dog()
    injector.register(dog, bind=Pet)

    assert injector.get(Pet) is dog

    injector.unregister(Pet)

    pytest.raises(injector.InjectorError, injector.get, Pet)


def test_unregister_not_registered_should_raise(fixture):
    pytest.raises(injector.InjectorError, injector.unregister, Pet)


class TestNamed:
    def test_named_register_get(self, fixture):
        dev = Dog()
        prod = Cat()
        injector.register(dev, bind=Pet, named='dev')
        injector.register(prod, bind=Pet, named='prod')

        assert injector.get(Pet, 'dev') is dev
        assert injector.get(Pet, 'prod') is prod

    def test_named_inject_descriptor(self, fixture):
        class Client:
            api: Pet = inject(named='prod')

        prod = Cat()
        injector.register(prod, bind=Pet, named='prod')

        assert Client().api is prod

    def test_named_get_not_registered_should_raise(self, fixture):
        pytest.raises(injector.InjectorError, injector.get, Pet, 'unknown')

    def test_named_unregister(self, fixture):
        prod = Cat()
        injector.register(prod, bind=Pet, named='prod')
        assert injector.get(Pet, 'prod') is prod

        injector.unregister(Pet, named='prod')
        pytest.raises(injector.InjectorError, injector.get, Pet, 'prod')


def test_get_with_string_as_arg_should_raise(fixture):
    pytest.raises(injector.InjectorError, injector.get, 'some-string')


# todo register with lazy initialization like register(lamda: Pet(), bind=Pet)
# todo use type hint on get() because now it looks like Any

class TestDataclasses:
    def test_dataclass(self, fixture):
        @dataclass
        class Dc:
            pet: Pet = inject()

        p = Pet()
        injector.register(p)
        dc = Dc()
        assert dc.pet is p


class TestGeneric:
    def test_register_generic(self, fixture):
        sc = SomeClass[Pet]()
        injector.register(sc, bind=SomeClass[Pet])

        assert injector.get(SomeClass[Pet]) is sc

        with pytest.raises(injector.InjectorError):
            injector.get(SomeClass[Dog])

    def test_register_generic_multiple_T(self, fixture):
        sc_dog = SomeClass[Dog]()
        injector.register(sc_dog, bind=SomeClass[Dog])

        sc_cat = SomeClass[Cat]()
        injector.register(sc_cat, bind=SomeClass[Cat])

        assert injector.get(SomeClass[Dog]) is sc_dog
        assert injector.get(SomeClass[Cat]) is sc_cat

    def test_inject_generic(self, fixture):
        class A:
            sc: SomeClass[Pet] = inject()

        sc = SomeClass[Pet]()
        injector.register(sc, bind=SomeClass[Pet])

        assert A().sc is sc


@pytest.fixture
def fixture():
    injector.default_injector.clear()
    yield
    injector.default_injector.clear()
