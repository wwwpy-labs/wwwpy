import pytest

from wwwpy.common import injector
from wwwpy.common.injector import inject


class Pet: ...


class Dog(Pet): ...


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


@pytest.fixture
def fixture():
    injector.default_injector.clear()
    yield
    injector.default_injector.clear()
