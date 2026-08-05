"""High-level Minecraft server connection: connect, keepalive, reconnect.

pyCraft is callback- and thread-based rather than async-native. The blocking
``connect``/``disconnect`` calls are bridged with ``asyncio.to_thread``, and
incoming packet listeners are registered as thread-safe callbacks. This module
is the only place where sync/async bridging is allowed in the project.
"""

import asyncio

import structlog
from minecraft.networking.connection import Connection

from miningcraft.protocol.handlers import EVENT_CONNECTED, EVENT_DISCONNECTED, EventBus

logger = structlog.get_logger(__name__)


class MinecraftConnection:
    """Owns a pyCraft connection and exposes an async lifecycle.

    Connection parameters (host, port, username) are injected per call so this
    layer never hardcodes or loads configuration. Config wiring happens in the
    Core Engine (v0.3.0).
    """

    def __init__(
        self, event_bus: EventBus, *, max_retries: int = 3, backoff_base: float = 1.0
    ) -> None:
        self._event_bus = event_bus
        self._max_retries = max_retries
        self._backoff_base = backoff_base

        self._connection: Connection | None = None
        self._connected = False
        self._host = ""
        self._port = 25565
        self._username = ""

    @property
    def is_connected(self) -> bool:
        """Whether a transport connection to the server is currently open."""
        return self._connected

    async def connect(
        self,
        host: str,
        port: int,
        username: str,
        *,
        version: str | None = None,
    ) -> bool:
        """Open a connection and log in as ``username``.

        Runs pyCraft's blocking connect off the event loop. Returns ``True``
        once the transport is up; login failures that occur after this point
        surface as ``OnDisconnected`` events.
        """
        if self._connected:
            logger.debug("connect_skipped", reason="already_connected")
            return True

        logger.info("connect_start", host=host, port=port, username=username)
        try:
            connection = Connection(
                host,
                port=port,
                username=username,
                initial_version=version,
                handle_exit=self._on_exit,
                handle_exception=self._on_exception,
            )
            await asyncio.to_thread(connection.connect)
        except Exception as exc:
            logger.error("connect_failed", host=host, port=port, error=str(exc))
            return False

        self._connection = connection
        self._host = host
        self._port = port
        self._username = username
        self._connected = True

        logger.info("connect_success", host=host, port=port)
        self._event_bus.publish(EVENT_CONNECTED, host=host, port=port, username=username)
        return True

    async def disconnect(self) -> None:
        """Terminate the connection."""
        if not self._connected and self._connection is None:
            return
        was_connected = self._connected
        self._connected = False
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                await asyncio.to_thread(connection.disconnect)
            except Exception as exc:
                logger.warning("disconnect_error", error=str(exc))
        logger.info("disconnect")
        if was_connected:
            self._event_bus.publish(EVENT_DISCONNECTED, host=self._host, port=self._port)

    def _on_exit(self) -> None:
        """Handle an unexpected connection termination from pyCraft's thread."""
        if self._connected:
            self._connected = False
            logger.info("connection_lost")
            self._event_bus.publish(EVENT_DISCONNECTED, host=self._host, port=self._port)

    def _on_exception(self, exc: BaseException, exc_info: object) -> None:
        """Handle a network error from pyCraft's thread."""
        was_connected = self._connected
        self._connected = False
        logger.error("connection_error", error=str(exc))
        if was_connected:
            self._event_bus.publish(EVENT_DISCONNECTED, host=self._host, port=self._port)
