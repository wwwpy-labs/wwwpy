from __future__ import annotations

import dataclasses
import inspect
from dataclasses import field
from typing import TypeVar, get_origin, Type


class InjectorError(Exception):
    pass


T = TypeVar('T')


class Injector:
    def __init__(self):
        self._registry = {}

    def bind(self, instance, *, to=None, named=None):
        """
        Register an instance with the injector.

        Args:
            instance: The instance to register
            to: Optional class to bind the instance to. If None, uses instance's class.
            named: Optional string key for named binding.

        Raises:
            InjectorError: If a dependency is already registered for the target class and named
        """
        if to is None:
            to = instance.__class__

        key = (to, named)
        if key in self._registry:
            raise InjectorError(f"Dependency already registered for {to!r} named={named!r}")

        self._registry[key] = instance

    def _unbind(self, bind, named=None):
        """
        Unregister a dependency.

        Args:
            bind: The class to unregister
            named: Optional string key for named binding.
        """
        key = (bind, named)
        if key in self._registry:
            del self._registry[key]
        else:
            raise InjectorError(f"No dependency registered for {bind!r} named={named!r}")

    def get(self, cls: type[T], named=None) -> T:
        """
        Get a registered instance for the given class (and optional named).

        Args:
            cls: The class to look up
            named: Optional string key for named binding.

        Returns:
            The registered instance

        Raises:
            InjectorError: If no dependency is registered for the class/named
        """
        # allow either a real class or a parametrized generic alias (e.g. SomeClass[Pet])
        if not (inspect.isclass(cls) or get_origin(cls) is not None):
            raise InjectorError(f"Expected a class, got `{cls}` of type {type(cls)}")

        key = (cls, named)
        if key not in self._registry:
            raise InjectorError(f"No dependency registered for {cls.__name__} named={named}")

        return self._registry[key]

    def _clear(self):
        """Clear all registered dependencies."""
        self._registry.clear()

    @property
    def field(self) -> Type[inject]:  # todo test
        return inject


default_injector = Injector()
injector = default_injector


class inject:
    """
    A data descriptor for injecting dependencies.

    Examples:
        class Service:
            # Inject a dependency using type annotation
            repository: Repository = inject()

        # Named injection
        class Client:
            api: ApiService = inject(name="prod")
    """

    def __init__(self, *, named=None):
        self.named = named
        self.injector = default_injector
        self.name = None
        self.cls = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:  # and is_dataclass(owner): # it is not yet a dataclass
            is_dataclass_in_doing = hasattr(owner, dataclasses._PARAMS) and \
                                    not dataclasses.is_dataclass(owner)
            if is_dataclass_in_doing:
                return field(init=False, default=self)

        if self.cls is None:
            ann = inspect.get_annotations(owner, eval_str=True)
            name = self.name
            if name in ann:
                self.cls = ann[name]
            else:
                raise InjectorError(f"Cannot find type annotation for {name} in {owner.__name__}")

        return self.injector.get(self.cls, self.named)

    def __set__(self, instance, value):
        raise InjectorError(f"Cannot set {self.name} directly. Use the injector to register a new instance.")
