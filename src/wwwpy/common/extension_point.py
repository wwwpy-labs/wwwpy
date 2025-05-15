from __future__ import annotations

import inspect
from typing import TypeVar, Generic

T = TypeVar('T')


class ExtensionPointRegistry(Generic[T]):

    def __init__(self, owner: type[T]):
        self._owner = owner
        self._extensions: list[T] = []
        self.base_type = owner

    def register(self, extension: T):
        if not isinstance(extension, self.base_type):
            raise ExtensionPointError(f'Expected {self.base_type}, got {type(extension)}')

        if extension in self._extensions:
            raise ExtensionPointError(f'Extension {extension} already registered')

        self._extensions.append(extension)

    def unregister(self, extension: T) -> bool:
        remove = extension in self._extensions
        if remove:
            self._extensions.remove(extension)
        return remove

    def _clear(self):
        """Used in tests to clear the registry"""
        self._extensions.clear()

    def __iter__(self):
        return iter(self._extensions)

    def __len__(self):
        return len(self._extensions)


class ExtensionPointError(Exception):
    pass


class ep_registry:

    def __init__(self):
        self._name = None
        self._ep_registry: ExtensionPointRegistry[...] = None

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, instance, owner):
        if self._ep_registry is None:
            try:
                ann = inspect.get_annotations(owner, eval_str=True)
            except:
                raise ExtensionPointError(f'Locally defined class are not supported. Cannot introspect {owner}')
            self._class_decl_frame = None
            descr_type = ann.get(self._name, None)
            self._ep_registry = ExtensionPointRegistry(owner)
            if not descr_type is ExtensionPointRegistry[owner]:
                raise ExtensionPointError(f'Expected {ExtensionPointRegistry[owner]}, got {descr_type}')
        return self._ep_registry

    def __set__(self, instance, value):
        raise ExtensionPointError(f"Cannot set {self._name}")
#
# import types
# import sys
# import functools
# def get_annotations(obj, *, globals=None, locals=None, eval_str=False):
#     """Compute the annotations dict for an object.
#
#     obj may be a callable, class, or module.
#     Passing in an object of any other type raises TypeError.
#
#     Returns a dict.  get_annotations() returns a new dict every time
#     it's called; calling it twice on the same object will return two
#     different but equivalent dicts.
#
#     This function handles several details for you:
#
#       * If eval_str is true, values of type str will
#         be un-stringized using eval().  This is intended
#         for use with stringized annotations
#         ("from __future__ import annotations").
#       * If obj doesn't have an annotations dict, returns an
#         empty dict.  (Functions and methods always have an
#         annotations dict; classes, modules, and other types of
#         callables may not.)
#       * Ignores inherited annotations on classes.  If a class
#         doesn't have its own annotations dict, returns an empty dict.
#       * All accesses to object members and dict values are done
#         using getattr() and dict.get() for safety.
#       * Always, always, always returns a freshly-created dict.
#
#     eval_str controls whether or not values of type str are replaced
#     with the result of calling eval() on those values:
#
#       * If eval_str is true, eval() is called on values of type str.
#       * If eval_str is false (the default), values of type str are unchanged.
#
#     globals and locals are passed in to eval(); see the documentation
#     for eval() for more information.  If either globals or locals is
#     None, this function may replace that value with a context-specific
#     default, contingent on type(obj):
#
#       * If obj is a module, globals defaults to obj.__dict__.
#       * If obj is a class, globals defaults to
#         sys.modules[obj.__module__].__dict__ and locals
#         defaults to the obj class namespace.
#       * If obj is a callable, globals defaults to obj.__globals__,
#         although if obj is a wrapped function (using
#         functools.update_wrapper()) it is first unwrapped.
#     """
#     if isinstance(obj, type):
#         # class
#         obj_dict = getattr(obj, '__dict__', None)
#         if obj_dict and hasattr(obj_dict, 'get'):
#             ann = obj_dict.get('__annotations__', None)
#             if isinstance(ann, types.GetSetDescriptorType):
#                 ann = None
#         else:
#             ann = None
#
#         obj_globals = None
#         module_name = getattr(obj, '__module__', None)
#         if module_name:
#             module = sys.modules.get(module_name, None)
#             if module:
#                 obj_globals = getattr(module, '__dict__', None)
#         obj_locals = dict(vars(obj))
#         unwrap = obj
#     elif isinstance(obj, types.ModuleType):
#         # module
#         ann = getattr(obj, '__annotations__', None)
#         obj_globals = getattr(obj, '__dict__')
#         obj_locals = None
#         unwrap = None
#     elif callable(obj):
#         # this includes types.Function, types.BuiltinFunctionType,
#         # types.BuiltinMethodType, functools.partial, functools.singledispatch,
#         # "class funclike" from Lib/test/test_inspect... on and on it goes.
#         ann = getattr(obj, '__annotations__', None)
#         obj_globals = getattr(obj, '__globals__', None)
#         obj_locals = None
#         unwrap = obj
#     else:
#         raise TypeError(f"{obj!r} is not a module, class, or callable.")
#
#     if ann is None:
#         return {}
#
#     if not isinstance(ann, dict):
#         raise ValueError(f"{obj!r}.__annotations__ is neither a dict nor None")
#
#     if not ann:
#         return {}
#
#     if not eval_str:
#         return dict(ann)
#
#     if unwrap is not None:
#         while True:
#             if hasattr(unwrap, '__wrapped__'):
#                 unwrap = unwrap.__wrapped__
#                 continue
#             if isinstance(unwrap, functools.partial):
#                 unwrap = unwrap.func
#                 continue
#             break
#         if hasattr(unwrap, "__globals__"):
#             obj_globals = unwrap.__globals__
#
#     if globals is None:
#         globals = obj_globals
#     if locals is None:
#         locals = obj_locals
#
#     return_value = {key:
#                         value if not isinstance(value, str) else eval(value, globals, locals)
#                     for key, value in ann.items() }
#     return return_value
