from __future__ import annotations

import inspect
import uuid
import weakref
from collections import defaultdict
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints

T = TypeVar('T')


class Subscription:
    """Represents an active subscription that can be canceled."""

    def __init__(self, event_bus: EventBus, event_type: Type, callback_id: str):
        self._event_bus = weakref.ref(event_bus)
        self._event_type = event_type
        self._callback_id = callback_id
        self._active = True

    def unsubscribe(self) -> bool:
        """Cancels this subscription."""
        if not self._active:
            return False

        event_bus = self._event_bus()
        if event_bus is None:
            self._active = False
            return False

        result = event_bus._remove_subscription(self._event_type, self._callback_id)
        self._active = False
        return result

    @property
    def is_active(self) -> bool:
        return self._active and self._event_bus() is not None


class EventBus:
    """Type-based event bus that routes events based on their Python types."""

    def __init__(self):
        # Maps event types to {callback_id: callback}
        self._subscribers: Dict[Type, Dict[str, Callable]] = defaultdict(dict)

    def subscribe(self, callback: Optional[Callable] = None, *, on: Optional[Type] = None) -> Subscription:
        """
        Subscribe to events of a specific type.

        Args:
            callback: Function to call when matching events are published
            on: Type of events to subscribe to. If None, inferred from callback type hints.

        Returns:
            A Subscription object that can be used to unsubscribe.
        """
        # If used as a decorator
        if callback is None:
            def decorator(func):
                return self.subscribe(func, on=on)

            return decorator

        # Try to infer the event type from callback signature if not explicitly provided
        event_type = on
        if event_type is None:
            hints = get_type_hints(callback)
            # Look for the first parameter's type hint
            sig = inspect.signature(callback)
            params = list(sig.parameters.values())
            if params and params[0].name in hints:
                event_type = hints[params[0].name]

        if event_type is None:
            raise ValueError("Could not determine event type. Please provide 'on' parameter or use type hints.")

        callback_id = str(uuid.uuid4())
        self._subscribers[event_type][callback_id] = callback
        return Subscription(self, event_type, callback_id)

    def publish(self, event: Any, *, on: Optional[Type] = None) -> int:
        """
        Publish an event to all subscribers of its type.

        Args:
            event: The event object to publish
            on: Optional specific type to publish on. If None, uses event's actual type.

        Returns:
            Number of callbacks notified
        """
        event_type = on if on is not None else type(event)

        # Ensure the event is actually of the specified type
        if on is not None and not isinstance(event, on):
            raise TypeError(f"Event {event} is not an instance of specified type {on}")

        count = 0
        # Direct subscribers to this exact type
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type].values():
                callback(event)
                count += 1

        return count

    def _remove_subscription(self, event_type: Type, callback_id: str) -> bool:
        """Remove a subscription by its ID. Returns True if successful."""
        if event_type in self._subscribers and callback_id in self._subscribers[event_type]:
            del self._subscribers[event_type][callback_id]
            # Clean up empty dicts
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]
            return True
        return False

    def clear(self) -> None:
        """Remove all subscriptions."""
        self._subscribers.clear()

    def get_subscriber_count(self, event_type: Type) -> int:
        """Get the number of subscribers for a specific event type."""
        return len(self._subscribers.get(event_type, {}))
