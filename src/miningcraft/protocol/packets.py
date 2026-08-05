"""Thin async wrappers around pyCraft's packet send/receive API.

pyCraft's ``Connection`` exposes thread-safe packet writing and callback-based
packet reception. This module adapts both to the project's async-first,
success/failure-returning conventions.
"""

from collections.abc import Callable

import structlog
from minecraft.networking.connection import Connection
from minecraft.networking.packets.packet import Packet

logger = structlog.get_logger(__name__)

PacketCallback = Callable[..., None]


class PacketSender:
    """Sends packets to the server, returning success/failure instead of raising."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    async def send(self, packet: Packet) -> bool:
        """Queue a packet for delivery to the server.

        pyCraft's ``write_packet`` is a non-blocking queue append; it is called
        directly and never raises on normal operation. On any failure this
        method logs and returns ``False``.
        """
        try:
            self._connection.write_packet(packet)
        except Exception as exc:
            logger.error("packet_send_failed", packet_type=type(packet).__name__, error=str(exc))
            return False
        logger.debug("packet_sent", packet_type=type(packet).__name__)
        return True


class PacketReceiver:
    """Receives packets via pyCraft callbacks and fans them out to listeners.

    pyCraft only supports *registering* listeners; it has no removal API. This
    receiver therefore keeps its own per-packet-type registry: one pyCraft hook
    per packet type forwards incoming packets to every registered callback, so
    listeners can be added and removed freely.
    """

    def __init__(self, connection: Connection) -> None:
        self._connection = connection
        self._listeners: dict[type[Packet], list[PacketCallback]] = {}

    def register_listener(self, packet_type: type[Packet], callback: PacketCallback) -> None:
        """Register a callback for a packet type.

        The first listener for a packet type installs a single pyCraft hook
        that dispatches subsequent packets of that type to all listeners.
        """
        listeners = self._listeners.setdefault(packet_type, [])
        if not listeners:
            self._connection.register_packet_listener(self._forward, packet_type)
        listeners.append(callback)
        logger.debug("listener_registered", packet_type=packet_type.__name__)

    def remove_listener(self, packet_type: type[Packet]) -> None:
        """Remove all listeners for a packet type.

        The underlying pyCraft hook cannot be unregistered, so it remains as a
        no-op once its callback list is empty.
        """
        listeners = self._listeners.pop(packet_type, None)
        if listeners:
            logger.debug("listener_removed", packet_type=packet_type.__name__, count=len(listeners))

    def _forward(self, packet: Packet) -> None:
        """Dispatch a received packet to all matching listeners."""
        for packet_type, listeners in self._listeners.items():
            if isinstance(packet, packet_type):
                logger.debug("packet_received", packet_type=type(packet).__name__)
                for callback in list(listeners):
                    callback(packet)
                return
