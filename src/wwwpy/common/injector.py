class InjectorError(Exception):
    pass


class Injector:
    def __init__(self):
        self._registry = {}

    def register(self, instance, bind=None):
        """
        Register an instance with the injector.

        Args:
            instance: The instance to register
            bind: Optional class to bind the instance to. If None, uses instance's class.

        Raises:
            InjectorError: If a dependency is already registered for the target class
        """
        if bind is None:
            bind = instance.__class__

        if bind in self._registry:
            raise InjectorError(f"Dependency already registered for {bind}")

        self._registry[bind] = instance

    def unregister(self, bind):
        """
        Unregister a dependency.

        Args:
            bind: The class to unregister
        """
        if bind in self._registry:
            del self._registry[bind]
        else:
            raise InjectorError(f"No dependency registered for {bind}")

    def get(self, cls):
        """
        Get a registered instance for the given class.

        Args:
            cls: The class to look up

        Returns:
            The registered instance

        Raises:
            InjectorError: If no dependency is registered for the class
        """
        if cls not in self._registry:
            raise InjectorError(f"No dependency registered for {cls}")

        return self._registry[cls]

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
    """

    def __init__(self, injector=None):
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

        return self.injector.get(self.cls)

    def __set__(self, instance, value):
        raise InjectorError(f"Cannot set {self.name} directly. Use the injector to register a new instance.")
