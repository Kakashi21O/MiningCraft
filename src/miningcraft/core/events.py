"""In-memory pub/sub event bus used for all inter-layer communication.

Events are the only allowed communication path between layers. ``publish``
invokes every registered handler for an event synchronously in subscription
order; an error raised by one handler is logged and never stops the others.
"""

from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)

EventHandler = Callable[..., Any]


class EventBus:
    """Pub/sub bus keyed by event name string.

    This class satisfies the ``EventBus`` protocol declared by the protocol
    layer (:mod:`miningcraft.protocol.handlers`), so it can be passed to
    ``MinecraftConnection`` unchanged.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register ``handler`` for ``event_name``.

        Subscribing the same handler twice is idempotent: it is stored once.
        """
        handlers = self._handlers.setdefault(event_name, [])
        if handler not in handlers:
            handlers.append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove ``handler`` from ``event_name``. Unknown pairs are ignored."""
        handlers = self._handlers.get(event_name)
        if handlers is None:
            return
        if handler in handlers:
            handlers.remove(handler)
        if not handlers:
            del self._handlers[event_name]

    def publish(self, event_name: str, **kwargs: Any) -> None:
        """Call every handler for ``event_name`` in subscription order.

        A handler that raises is logged and does not prevent the remaining
        handlers from running.
        """
        handlers = list(self._handlers.get(event_name, ()))
        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception:
                logger.exception("event_handler_error", event_name=event_name, handler=handler)

    def clear(self, event_name: str | None = None) -> None:
        """Remove all handlers, or all handlers for a single event name."""
        if event_name is None:
            self._handlers.clear()
        else:
            self._handlers.pop(event_name, None)
