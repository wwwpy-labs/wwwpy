from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Generic

import pytest

from wwwpy.common.injectorlib import inject, injector, InjectorError


class Pet: ...


class Dog(Pet): ...


class Cat(Pet): ...


_T = TypeVar('_T')


class SomeClass(Generic[_T]): ...


@pytest.fixture
def fixture():
    injector._clear()
    yield
    injector._clear()


def test_bind_get(fixture):
    pet = Pet()
    injector.bind(pet)

    assert pet is injector.get(Pet)


def test_inject_descriptor(fixture):
    class A:
        pet: Pet = inject()

    p = Pet()
    injector.bind(p)

    assert A().pet is p


def test_inject_descriptor_set__should_raise(fixture):
    class A:
        pet: Pet = inject()

    p = Pet()
    injector.bind(p)

    with pytest.raises(InjectorError):
        setattr(A(), 'pet', Dog())


def test_polymorphism(fixture):
    dog = Dog()

    injector.bind(dog, to=Pet)

    assert injector.get(Pet) is dog


def test_bind_multiple_should_throw(fixture):
    dog = Dog()
    injector.bind(dog, to=Pet)

    with pytest.raises(InjectorError):
        injector.bind(dog, to=Pet)


def test_unbind(fixture):
    dog = Dog()
    injector.bind(dog, to=Pet)

    assert injector.get(Pet) is dog

    injector._unbind(Pet)

    with pytest.raises(InjectorError):
        injector.get(Pet)


def test_unbind_not_binded_should_raise(fixture):
    with pytest.raises(InjectorError):
        injector._unbind(Pet)


class TestNamed:
    def test_named_register_get(self, fixture):
        dev = Dog()
        prod = Cat()
        injector.bind(dev, to=Pet, named='dev')
        injector.bind(prod, to=Pet, named='prod')

        assert injector.get(Pet, 'dev') is dev
        assert injector.get(Pet, 'prod') is prod

    def test_named_inject_descriptor(self, fixture):
        class Client:
            api: Pet = inject(named='prod')

        prod = Cat()
        injector.bind(prod, to=Pet, named='prod')

        assert Client().api is prod

    def test_named_get_not_binded_should_raise(self, fixture):
        with pytest.raises(InjectorError):
            injector.get(Pet, 'unknown')

    def test_named_unbind(self, fixture):
        prod = Cat()
        injector.bind(prod, to=Pet, named='prod')
        assert injector.get(Pet, 'prod') is prod

        injector._unbind(Pet, named='prod')
        pytest.raises(InjectorError, injector.get, Pet, 'prod')


def test_get_with_string_as_arg_should_raise(fixture):
    pytest.raises(InjectorError, injector.get, 'some-string')


# todo bind with lazy initialization like bind(lamda: Pet(), bind=Pet)
# todo use type hint on get() because now it looks like Any

class TestDataclasses:
    def test_dataclass(self, fixture):
        @dataclass
        class Dc:
            pet: Pet = inject()

        p = Pet()
        injector.bind(p)
        dc = Dc()
        assert dc.pet is p


class TestGeneric:
    def test_bind_generic(self, fixture):
        sc = SomeClass[Pet]()
        injector.bind(sc, to=SomeClass[Pet])

        assert injector.get(SomeClass[Pet]) is sc

        with pytest.raises(InjectorError):
            injector.get(SomeClass[Dog])

    def test_bind_generic_multiple_T(self, fixture):
        sc_dog = SomeClass[Dog]()
        injector.bind(sc_dog, to=SomeClass[Dog])

        sc_cat = SomeClass[Cat]()
        injector.bind(sc_cat, to=SomeClass[Cat])

        assert injector.get(SomeClass[Dog]) is sc_dog
        assert injector.get(SomeClass[Cat]) is sc_cat

    def test_inject_generic(self, fixture):
        class A:
            sc: SomeClass[Pet] = inject()

        sc = SomeClass[Pet]()
        injector.bind(sc, to=SomeClass[Pet])

        assert A().sc is sc


class TestStaticAccess:
    def test_static_binding(self, fixture):
        class Class1:
            EP_LIST: Pet = inject()

        pet = Pet()
        injector.bind(pet)

        assert Class1.EP_LIST is pet
        assert Class1().EP_LIST is pet

    def test_static_binding_dc(self, fixture):
        @dataclass
        class Class1:
            EP_LIST: Pet = inject()

        pet = Pet()
        injector.bind(pet)

        assert Class1.EP_LIST is pet
        assert Class1().EP_LIST is pet
