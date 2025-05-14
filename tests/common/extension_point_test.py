from __future__ import annotations

import pytest

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry, ExtensionPointError


class SomeInterface1:
    EP_REGISTRY: ExtensionPointRegistry[SomeInterface1] = ep_registry()


def test_should_introspect_the_correct_class():
    assert SomeInterface1.EP_REGISTRY.base_type is SomeInterface1


class SomeGlobal: ...


class SomeInterface2:
    EP_REGISTRY: ExtensionPointRegistry[SomeGlobal] = ep_registry()


def test_the_generic_type_must_be_the_same_as_the_owner():
    with pytest.raises(ExtensionPointError):
        x = SomeInterface2.EP_REGISTRY


class SomeInterface3:
    EP_REGISTRY: ExtensionPointRegistry[SomeInterface3] = ep_registry()


def test_should_return_correct_instance():
    instance = SomeInterface3.EP_REGISTRY
    assert instance is SomeInterface3.EP_REGISTRY
    assert isinstance(instance, ExtensionPointRegistry)


class SomeInterface4:
    EP_REGISTRY: ExtensionPointRegistry[SomeInterface4] = ep_registry()


def test_register():
    class SomeImpl(SomeInterface4):
        pass

    impl = SomeImpl()
    SomeInterface4.EP_REGISTRY.register(impl)

    assert (impl,) == SomeInterface4.EP_REGISTRY.extensions


class SomeInterface5:
    EP_REGISTRY: ExtensionPointRegistry[SomeInterface5] = ep_registry()


def test_register_should_be_type_safe():
    class Some:
        pass

    with pytest.raises(ExtensionPointError):
        SomeInterface5.EP_REGISTRY.register(Some())


def test_locally_defined_extension_point_are_not_supported():
    class SomeInterface:
        EP_REGISTRY: ExtensionPointRegistry[SomeInterface] = ep_registry()

    with pytest.raises(ExtensionPointError):
        x = SomeInterface.EP_REGISTRY
