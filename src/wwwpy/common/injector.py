import inspect
from dataclasses import field
from typing import TypeVar


class InjectorError(Exception):
    pass


T = TypeVar('T')

class Injector:
    def __init__(self):
        self._registry = {}

    def register(self, instance, *, bind=None, named=None):
        """
        Register an instance with the injector.

        Args:
            instance: The instance to register
            bind: Optional class to bind the instance to. If None, uses instance's class.
            named: Optional string key for named binding.

        Raises:
            InjectorError: If a dependency is already registered for the target class and named
        """
        if bind is None:
            bind = instance.__class__

        key = (bind, named)
        if key in self._registry:
            raise InjectorError(f"Dependency already registered for {bind!r} named={named!r}")

        self._registry[key] = instance

    def unregister(self, bind, named=None):
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
        if not inspect.isclass(cls):
            raise InjectorError(f"Expected a class, got `{cls}` of type {type(cls)}")
        key = (cls, named)
        if key not in self._registry:
            raise InjectorError(f"No dependency registered for {cls.__name__} named={named}")

        return self._registry[key]

    def clear(self):
        """Clear all registered dependencies."""
        self._registry.clear()


# Create the default injector
# todo evaluate if renaming this module to injectorlib.py and default_inject to injector
#  and reference injector.register() and injector.get() and injector.unregister() everywhere
#  instead of only 'register()'
default_injector = Injector()

# Create convenience functions that delegate to the default injector
register = default_injector.register
unregister = default_injector.unregister


def get(cls: type[T], named=None) -> T:
    return default_injector.get(cls, named)

# def inject(named=None, injector=None):
#     return _inject(named=named, injector=injector)

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

    def __init__(self, *, named=None, injector=None):
        self.named = named
        self.injector = injector or default_injector
        self.name = None
        self.cls = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:  # and is_dataclass(owner): # it is not yet a dataclass
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
