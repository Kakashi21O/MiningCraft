"""In-memory pub/sub event bus used for all inter-layer communication.

Events are the only allowed communication path between layers. ``publish``
invokes every registered handler for an event synchronously in subscription
order; an error raised by one handler is logged and never stops the others.

The bus is thread-safe: handlers are registered from pyCraft's network thread
and published from both the event loop and that same thread, so every handler
list mutation happens under a re-entrant lock.
"""

import inspect
import threading
from collections.abc import Callable
from typing import Any

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
        self._lock = threading.RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Register ``handler`` for ``event_name``.

        Subscribing the same handler twice is idempotent: it is stored once.
        """
        with self._lock:
            handlers = self._handlers.setdefault(event_name, [])
            if handler not in handlers:
                handlers.append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove ``handler`` from ``event_name``. Unknown pairs are ignored."""
        with self._lock:
            handlers = self._handlers.get(event_name)
            if handlers is None:
                return
            if handler in handlers:
                handlers.remove(handler)
            if not handlers:
                del self._handlers[event_name]

    def publish(self, event_name: str, **kwargs: Any) -> None:
        """Call every handler for ``event_name`` in subscription order.

        Handlers are copied under the lock and invoked outside it, so a handler
        that subscribes or unsubscribes cannot deadlock the bus. A handler that
        raises is logged and does not prevent the remaining handlers running.
        """
        with self._lock:
            handlers = list(self._handlers.get(event_name, ()))
        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception:
                logger.exception("event_handler_error", event_name=event_name, handler=handler)

    async def publish_async(self, event_name: str, **kwargs: Any) -> None:
        """Invoke handlers for ``event_name``, awaiting async ones.

        Sync handlers run as-is; async handlers are awaited. Intended for
        callers that run inside an event loop and need handler results.
        """
        with self._lock:
            handlers = list(self._handlers.get(event_name, ()))
        for handler in handlers:
            try:
                result = handler(**kwargs)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("event_handler_error", event_name=event_name, handler=handler)

    def clear(self, event_name: str | None = None) -> None:
        """Remove all handlers, or all handlers for a single event name."""
        with self._lock:
            if event_name is None:
                self._handlers.clear()
            else:
                self._handlers.pop(event_name, None)
