from __future__ import annotations

import logging
import types
import weakref
from dataclasses import dataclass

logger = logging.getLogger(__name__)

import js
from pyodide.ffi import create_proxy
from pyodide.ffi.wrappers import add_event_listener, remove_event_listener, EVENT_LISTENERS


@dataclass
class Accept:
    target: js.EventTarget
    type: str


_js_attrs = dict()


def convention_accept(name: str) -> Accept | None:
    """This accepts methods with the format _js_window__click, _js_document__keydown, etc."""
    # Check if the string starts with "_js_"
    if not name.startswith('_js_'):
        return None

    # Find the position of "__"
    double_underscore_pos = name.find('__', 4)  # Start searching after "_js_"
    if double_underscore_pos == -1:
        return None

    target_name = name[4:double_underscore_pos]
    event_type = name[double_underscore_pos + 2:]

    # Check if target_name and event_type are not empty
    if not target_name or not event_type:
        return None

    # Map target_name to JS object
    target_obj = getattr(js, target_name, None)
    if target_obj is None:
        return None

    target_obj_stored = _js_attrs.get(target_name, None)
    if target_obj_stored is None:
        _js_attrs[target_name] = target_obj
    else:
        if target_obj.js_id != target_obj_stored.js_id:
            msg = f'js_id mismatch for {target_name}: {target_obj.js_id} != {target_obj.js_id}'
            raise RuntimeError(msg)

    logger.debug(f'target_name={target_name} target_obj.js_id={target_obj.js_id} event_type={event_type}')
    return Accept(target_obj, event_type)


def _process_event_listeners(target, action_func, accept=convention_accept):
    """
    Helper function to process event listeners for methods in target.

    Args:
        target: The object containing methods to process
        action_func: Function to call with (target, event_type, method) for matched methods
        accept: A function that determines if a method matches the event handler pattern
    """
    for name in dir(target):
        if name.startswith('__'):
            continue

        attr = getattr(target, name)
        if callable(attr):
            accepted = accept(name)
            if accepted is not None:
                logger.debug(f'calling {action_func.__name__} for {name} js_id={accepted.target.js_id}')
                try:
                    action_func(accepted.target, accepted.type, attr)
                except KeyError as e:
                    logger.error(f'KeyError: {e} for {name}')
                    logger.info(f'target=`{target.__class__.__name__}` has no event listener for {name}')
                logger.info(f'EVENT_LISTENERS=`{EVENT_LISTENERS}`')


def add_event_listeners(target, accept=convention_accept):
    """
    Add event listeners to methods in target that match the naming convention.

    Args:
        target: The object containing methods to be used as event handlers
        accept: A function that determines if a method should be used as an event handler
    """
    c = _counter(target)
    _counter(target, 1)

    if c > 0:
        logger.debug(f'target={target.__class__.__name__} already has {c} event listeners installed, skipping')
        return
    logger.debug(f'target={target.__class__.__name__} has no event listeners installed, adding')
    _process_event_listeners(target, add_event_listener, accept)


def remove_event_listeners(target, accept=convention_accept):
    """
    Remove event listeners from methods in target that match the naming convention.

    Args:
        target: The object containing methods that were used as event handlers
        accept: A function that determines if a method was used as an event handler
    """
    c = _counter(target, -1)
    if c != 0:
        logger.debug(f'target={target.__class__.__name__} still has {c} event listeners installed, not removing')
        return
    logger.debug(f'target={target.__class__.__name__} has no event listeners installed, removing')
    _process_event_listeners(target, remove_event_listener, accept)


def _counter(target, amount=0) -> int:
    if not hasattr(target, '_install_count'):
        target._install_count = 0
    target._install_count += amount
    return target._install_count


class HandlerOptions:
    def __init__(self, func: callable, target: js.EventTarget, type: str):
        self.func = func
        self.target: js.EventTarget = target
        self.type: str = type

    def install_event(self, h: Handler):
        self.target.addEventListener(self.type, h.proxy)


def _get_handler_options(func) -> HandlerOptions:
    if not hasattr(func, '_handler_options'):
        raise ValueError('handler_options not set for this function')
    return func._handler_options


def handler_options(target, type):
    def decorator(func):
        # only class type methods (not class instance methods here)
        func._handler_options = HandlerOptions(func, target, type)
        return func

    return decorator


class Handler:
    _instance: weakref.ref
    _class_func: types.FunctionType

    def __init__(self, instance, class_func: callable):
        self._instance = weakref.ref(instance)
        self._class_func = class_func
        # Only bound methods: wrap in WeakMethod
        self._install_count = 0
        self._strong_ref = None
        self._proxy = None

    @property
    def bound_method(self) -> callable:
        inst = self._instance()
        if inst is None:
            raise ReferenceError(f"target instance has been garbage‑collected; func={self._class_func.__name__}")
        bm = self._class_func.__get__(inst, self._class_func.__class__)
        return bm

    def install(self):
        ho = _get_handler_options(self._class_func)
        c = _counter(self, 1)
        logger.debug(f'target={ho.__class__.__name__} counter={c} for {ho.type}')

        if c > 1:
            return
        self._proxy = create_proxy(self.bound_method)  # this will create a circular reference, to avoid gc of func
        ho.target.addEventListener(ho.type, self._proxy)


from weakref import WeakKeyDictionary

_instances: WeakKeyDictionary[object, dict] = WeakKeyDictionary()


def _instances_dict(instance: object) -> dict:
    i = _instances.get(instance, None)
    if i is None:
        i = dict()
        _instances[instance] = i
    return i


def handler(bound_method: types.MethodType | callable) -> Handler:
    assert isinstance(bound_method, types.MethodType), "method_storage() requires a bound method"
    # only class instance methods (not class type methods here)
    instance = bound_method.__self__
    instance_dict = _instances_dict(instance)
    mf = bound_method.__func__
    handler = instance_dict.get(mf, None)
    if handler is None:
        handler = Handler(instance, mf)
        instance_dict[mf] = handler

    return handler
