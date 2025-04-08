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


def add_event_listeners(target, accept=convention_accept):
    """
    Add event listeners to methods in target that match the naming convention.

    Args:
        target: The object containing methods to be used as event handlers
        accept: A function that determines if a method should be used as an event handler
    """

    # Get all attributes (potential methods) of the target
    for name in dir(target):
        # Skip special methods
        if name.startswith('__'):
            continue

        attr = getattr(target, name)
        # Check if it's callable (a method)
        if callable(attr):
            # Use the accept function to check if this method should be an event handler
            accepted = accept(name)
            if accepted is not None:
                # Create a proxy of the method for JavaScript
                add_event_listener(accepted.target, accepted.type, attr)


def remove_event_listeners(target, accept=convention_accept):
    """
    Remove event listeners from methods in target that match the naming convention.

    Args:
        target: The object containing methods that were used as event handlers
        accept: A function that determines if a method was used as an event handler
    """
    # Get all attributes (potential methods) of the target
    for name in dir(target):
        # Skip special methods
        if name.startswith('__'):
            continue

        attr = getattr(target, name)
        # Check if it's callable (a method)
        if callable(attr):
            # Use the accept function to check if this method was an event handler
            accepted = accept(name)
            if accepted is not None:
                # Remove the event listener
                remove_event_listener(accepted.target, accepted.type, attr)
