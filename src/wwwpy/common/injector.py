class InjectorError(Exception):
    pass


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

    def get(self, cls, named=None):
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
        key = (cls, named)
        if key not in self._registry:
            raise InjectorError(f"No dependency registered for {cls!r} named={named!r}")

        return self._registry[key]

    def clear(self):
        """Clear all registered dependencies."""
        self._registry.clear()


# Create the default injector
default_injector = Injector()

# Create convenience functions that delegate to the default injector
register = default_injector.register
unregister = default_injector.unregister
get = default_injector.get


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
        # Try to get the type from annotations
        if hasattr(owner, "__annotations__") and name in owner.__annotations__:
            self.cls = owner.__annotations__[name]

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if self.cls is None:
            raise InjectorError(f"No type annotation for {self.name}")

        return self.injector.get(self.cls, self.named)

    def __set__(self, instance, value):
        raise InjectorError(f"Cannot set {self.name} directly. Use the injector to register a new instance.")
