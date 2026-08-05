"""Packet-to-event dispatch for the protocol layer.

Maps incoming pyCraft packets to core event names. Handlers perform zero
game logic: they only dispatch the event name plus the raw packet object.
"""

from typing import Protocol

import structlog
from minecraft.networking.packets.clientbound.play import (
    BlockChangePacket,
    ChatMessagePacket,
    DisconnectPacket,
    KeepAlivePacket,
    PlayerPositionAndLookPacket,
    SpawnObjectPacket,
)

from miningcraft.protocol.packets import PacketReceiver

logger = structlog.get_logger(__name__)

# Event names emitted by the protocol layer. Consumed by the Core Engine (v0.3.0).
EVENT_CONNECTED = "OnConnected"
EVENT_DISCONNECTED = "OnDisconnected"
EVENT_CHUNK_LOADED = "OnChunkLoaded"
EVENT_CHUNK_UNLOADED = "OnChunkUnloaded"
EVENT_PLAYER_POSITION_UPDATE = "OnPlayerPositionUpdate"
EVENT_ENTITY_SPAWN = "OnEntitySpawn"
EVENT_ENTITY_DESPAWN = "OnEntityDespawn"
EVENT_INVENTORY_UPDATE = "OnInventoryUpdate"
EVENT_BLOCK_CHANGE = "OnBlockChange"
EVENT_CHAT_MESSAGE = "OnChatMessage"
EVENT_KEEP_ALIVE = "OnKeepAlive"


class EventBus(Protocol):
    """Minimal publish interface used by the protocol layer."""

    def publish(self, event_name: str, **kwargs: object) -> None: ...


class PacketHandlerRegistry:
    """Registers pyCraft packet listeners that dispatch events with raw data."""

    def __init__(self) -> None:
        self._receiver: PacketReceiver | None = None
        self._event_bus: EventBus | None = None

    def register_all(self, receiver: PacketReceiver, event_bus: EventBus) -> None:
        """Bind packet listeners to a receiver and event bus.

        Only packets provided by pyCraft master are registered. The chunk,
        entity-despawn, and inventory packets are not yet supported by pyCraft
        (see ADR 012), so ``OnChunkLoaded``, ``OnChunkUnloaded``,
        ``OnEntityDespawn``, and ``OnInventoryUpdate`` stay undeclared until a
        protocol library with those packets is adopted.
        """
        self._receiver = receiver
        self._event_bus = event_bus
        receiver.register_listener(PlayerPositionAndLookPacket, self._on_player_position_update)
        receiver.register_listener(BlockChangePacket, self._on_block_change)
        receiver.register_listener(SpawnObjectPacket, self._on_entity_spawn)
        receiver.register_listener(ChatMessagePacket, self._on_chat_message)
        receiver.register_listener(DisconnectPacket, self._on_disconnect)
        receiver.register_listener(KeepAlivePacket, self._on_keep_alive)

    def _publish(self, event_name: str, packet: object) -> None:
        if self._event_bus is not None:
            self._event_bus.publish(event_name, packet=packet)
        else:
            logger.warning("event_bus_not_bound", event_name=event_name)

    def _on_player_position_update(self, packet: PlayerPositionAndLookPacket) -> None:
        self._publish(EVENT_PLAYER_POSITION_UPDATE, packet)

    def _on_block_change(self, packet: BlockChangePacket) -> None:
        self._publish(EVENT_BLOCK_CHANGE, packet)

    def _on_entity_spawn(self, packet: SpawnObjectPacket) -> None:
        self._publish(EVENT_ENTITY_SPAWN, packet)

    def _on_chat_message(self, packet: ChatMessagePacket) -> None:
        self._publish(EVENT_CHAT_MESSAGE, packet)

    def _on_disconnect(self, packet: DisconnectPacket) -> None:
        self._publish(EVENT_DISCONNECTED, packet)

    def _on_keep_alive(self, packet: KeepAlivePacket) -> None:
        self._publish(EVENT_KEEP_ALIVE, packet)
