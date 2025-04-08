from __future__ import annotations

from dataclasses import dataclass

import js
from pyodide.ffi import create_proxy
from pyodide.ffi.wrappers import add_event_listener, remove_event_listener


@dataclass
class Accept:
    target: js.EventTarget
    type: str


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
                action_func(accepted.target, accepted.type, attr)


def add_event_listeners(target, accept=convention_accept):
    """
    Add event listeners to methods in target that match the naming convention.

    Args:
        target: The object containing methods to be used as event handlers
        accept: A function that determines if a method should be used as an event handler
    """
    _process_event_listeners(target, add_event_listener, accept)


def remove_event_listeners(target, accept=convention_accept):
    """
    Remove event listeners from methods in target that match the naming convention.

    Args:
        target: The object containing methods that were used as event handlers
        accept: A function that determines if a method was used as an event handler
    """
    _process_event_listeners(target, remove_event_listener, accept)
