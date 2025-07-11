from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Event:
    """Base event class"""
    name: str
    data: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Event bus for decoupled communication"""
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
    
    def subscribe(self, event_name: str, handler: Callable) -> None:
        """Subscribe to an event"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def publish(self, event: Event) -> None:
        """Publish an event"""
        if handlers := self._handlers.get(event.name):
            for handler in handlers:
                handler(event)
    
    def unsubscribe(self, event_name: str, handler: Callable) -> None:
        """Unsubscribe from an event"""
        if event_name in self._handlers:
            self._handlers[event_name].remove(handler)