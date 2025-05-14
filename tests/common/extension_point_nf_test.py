"""no future imports"""
import pytest

from wwwpy.common.extension_point import EPRegistry, ep_registry, ExtensionPointError


def test_the_generic_type_must_be_the_same_as_the_owner():
    class Some: ...

    class SomeInterface:
        EP_REGISTRY: EPRegistry[Some] = ep_registry()

    with pytest.raises(ExtensionPointError):
        x = SomeInterface.EP_REGISTRY


class SomeGlobal: ...


def test_the_generic_type_must_be_the_same_as_the_owner_global():
    class SomeInterface:
        EP_REGISTRY: EPRegistry[SomeGlobal] = ep_registry()

    with pytest.raises(ExtensionPointError):
        x = SomeInterface.EP_REGISTRY
