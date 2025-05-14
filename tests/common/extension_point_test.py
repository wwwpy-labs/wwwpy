from __future__ import annotations

import pytest

from wwwpy.common.extension_point import EPRegistry, ep_registry, ExtensionPointError


def test_should_introspect_the_correct_class():
    class SomeInterface:
        EP_REGISTRY: EPRegistry[SomeInterface] = ep_registry()

    assert SomeInterface.EP_REGISTRY.base_type is SomeInterface


def test_the_generic_type_must_be_the_same_as_the_owner():
    class Some: ...

    class SomeInterface:
        EP_REGISTRY: EPRegistry[Some] = ep_registry()

    with pytest.raises(ExtensionPointError):
        x = SomeInterface.EP_REGISTRY


def test_the_generic_type_must_be_the_same_as_the_owner_decl_after():
    class SomeInterface:
        EP_REGISTRY: EPRegistry[Some] = ep_registry()

    class Some: ...

    with pytest.raises(ExtensionPointError):
        x = SomeInterface.EP_REGISTRY


def test_should_return_correct_instance():
    class SomeInterface:
        EP_REGISTRY: EPRegistry[SomeInterface] = ep_registry()

    instance = SomeInterface.EP_REGISTRY
    assert instance is SomeInterface.EP_REGISTRY
    assert isinstance(instance, EPRegistry)


def test_register():
    class SomeInterface:
        EP_REGISTRY: EPRegistry[SomeInterface] = ep_registry()

    class SomeImpl(SomeInterface):
        pass

    impl = SomeImpl()
    SomeInterface.EP_REGISTRY.register(impl)

    assert [impl] == SomeInterface.EP_REGISTRY.extensions


def test_register_should_be_type_safe():
    class SomeInterface:
        EP_REGISTRY: EPRegistry[SomeInterface] = ep_registry()

    class Some:
        pass

    with pytest.raises(ExtensionPointError):
        SomeInterface.EP_REGISTRY.register(Some())
