"""Unit tests for PacketHandlerRegistry packet-to-event dispatch."""

from uuid import uuid4

import pytest
from minecraft.networking.packets.clientbound.play import (
    BlockChangePacket,
    ChatMessagePacket,
    DisconnectPacket,
    KeepAlivePacket,
    PlayerPositionAndLookPacket,
    SpawnObjectPacket,
)

from miningcraft.protocol.handlers import (
    EVENT_BLOCK_CHANGE,
    EVENT_CHAT_MESSAGE,
    EVENT_CHUNK_LOADED,
    EVENT_CHUNK_UNLOADED,
    EVENT_DISCONNECTED,
    EVENT_ENTITY_DESPAWN,
    EVENT_ENTITY_SPAWN,
    EVENT_INVENTORY_UPDATE,
    EVENT_KEEP_ALIVE,
    EVENT_PLAYER_POSITION_UPDATE,
    PacketHandlerRegistry,
)
from miningcraft.protocol.packets import PacketReceiver


@pytest.fixture
def receiver(mocker) -> PacketReceiver:
    return PacketReceiver(mocker.MagicMock())


@pytest.fixture
def registry(event_bus) -> PacketHandlerRegistry:
    handler = PacketHandlerRegistry()
    return handler


def bind(receiver, event_bus) -> PacketHandlerRegistry:
    handler = PacketHandlerRegistry()
    handler.register_all(receiver, event_bus)
    return handler


def test_position_packet_dispatches_event(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = PlayerPositionAndLookPacket()
    packet.x, packet.feet_y, packet.z = 1.0, 2.0, 3.0

    receiver._forward(packet)

    event_bus.assert_published(EVENT_PLAYER_POSITION_UPDATE)
    event_name, kwargs = event_bus.published[-1]
    assert event_name == EVENT_PLAYER_POSITION_UPDATE
    assert kwargs["packet"] is packet


def test_block_change_packet_dispatches_event(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = BlockChangePacket()
    packet.block_state_id = 123

    receiver._forward(packet)

    event_bus.assert_published(EVENT_BLOCK_CHANGE)
    assert event_bus.published[-1][1]["packet"] is packet


def test_entity_spawn_packet_dispatches_event(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = SpawnObjectPacket()
    packet.entity_id = 7
    packet.object_uuid = uuid4()

    receiver._forward(packet)

    event_bus.assert_published(EVENT_ENTITY_SPAWN)


def test_chat_message_packet_dispatches_event(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = ChatMessagePacket()
    packet.json_data = '{"text": "hello"}'

    receiver._forward(packet)

    event_bus.assert_published(EVENT_CHAT_MESSAGE)


def test_disconnect_packet_dispatches_event(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = DisconnectPacket()
    packet.json_data = '{"text": "Server closed"}'

    receiver._forward(packet)

    event_bus.assert_published(EVENT_DISCONNECTED)


def test_keepalive_packet_dispatches_event(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = KeepAlivePacket()
    packet.keep_alive_id = 42

    receiver._forward(packet)

    event_bus.assert_published(EVENT_KEEP_ALIVE)


def test_handler_dispatches_no_game_logic(receiver, event_bus) -> None:
    bind(receiver, event_bus)
    packet = PlayerPositionAndLookPacket()
    packet.x, packet.feet_y, packet.z = 10.5, 64.0, -20.25
    packet.yaw, packet.pitch, packet.on_ground = 90.0, 0.0, True
    before = (packet.x, packet.feet_y, packet.z, packet.yaw, packet.pitch, packet.on_ground)

    receiver._forward(packet)

    after = (packet.x, packet.feet_y, packet.z, packet.yaw, packet.pitch, packet.on_ground)
    assert after == before
    assert event_bus.published[-1][1]["packet"] is packet


def test_register_all_binds_supported_packets_only(receiver, event_bus) -> None:
    bind(receiver, event_bus)

    assert receiver._connection.register_packet_listener.call_count == 6


def test_deferred_events_stay_declared(receiver, event_bus) -> None:
    """Chunk/despawn/inventory events are declared but not bindable on pyCraft master."""
    for event_name in (
        EVENT_CHUNK_LOADED,
        EVENT_CHUNK_UNLOADED,
        EVENT_ENTITY_DESPAWN,
        EVENT_INVENTORY_UPDATE,
    ):
        assert isinstance(event_name, str)
