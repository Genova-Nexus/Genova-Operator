"""Thread-safe Publish-Subscribe Event Bus for Genova Operator.

Enables decoupled, event-driven communication between core components, sub-systems,
and external listeners such as Genova Nexus.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Dict, List, Optional, Set

from genova_operator.core.types import OperatorEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[OperatorEvent], None]


class EventBus:
    """Thread-safe event bus supporting topic-based pub/sub pattern."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: Dict[str, Set[EventHandler]] = {}
        self._global_subscribers: Set[EventHandler] = set()

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler callback to a specific event type.

        Args:
            event_type: Event type string to listen for (or '*' for all events).
            handler: Callable taking an OperatorEvent instance.
        """
        with self._lock:
            if event_type == "*":
                self._global_subscribers.add(handler)
            else:
                if event_type not in self._subscribers:
                    self._subscribers[event_type] = set()
                self._subscribers[event_type].add(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """Unsubscribe a handler callback from an event type.

        Args:
            event_type: Event type string (or '*' for global subscribers).
            handler: Callable to remove.

        Returns:
            True if handler was found and removed, False otherwise.
        """
        with self._lock:
            if event_type == "*":
                if handler in self._global_subscribers:
                    self._global_subscribers.remove(handler)
                    return True
                return False
            elif event_type in self._subscribers:
                if handler in self._subscribers[event_type]:
                    self._subscribers[event_type].remove(handler)
                    if not self._subscribers[event_type]:
                        del self._subscribers[event_type]
                    return True
            return False

    def publish(self, event: OperatorEvent) -> None:
        """Publish an event to all registered topic and global subscribers.

        Args:
            event: OperatorEvent instance to dispatch.
        """
        with self._lock:
            topic_handlers = list(self._subscribers.get(event.event_type, set()))
            global_handlers = list(self._global_subscribers)

        handlers = topic_handlers + global_handlers

        for handler in handlers:
            try:
                handler(event)
            except Exception as err:
                logger.exception(
                    "Error executing event handler %r for event %s: %s",
                    handler,
                    event.event_type,
                    err,
                )

    def clear(self) -> None:
        """Clear all registered event subscribers."""
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()

    def subscriber_count(self, event_type: Optional[str] = None) -> int:
        """Return count of registered subscribers for an event type or total."""
        with self._lock:
            if event_type == "*":
                return len(self._global_subscribers)
            elif event_type is not None:
                return len(self._subscribers.get(event_type, set()))
            else:
                total_topic = sum(len(handlers) for handlers in self._subscribers.values())
                return total_topic + len(self._global_subscribers)
