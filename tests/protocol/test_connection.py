"""Unit tests for MinecraftConnection using a mocked pyCraft connection."""

from minecraft.networking.packets.clientbound.play import KeepAlivePacket

from miningcraft.protocol.connection import MinecraftConnection
from miningcraft.protocol.handlers import EVENT_CONNECTED, EVENT_DISCONNECTED


def make_connection(event_bus, **kwargs) -> MinecraftConnection:
    return MinecraftConnection(event_bus, max_retries=3, backoff_base=0.0, **kwargs)


async def test_connect_success(event_bus, mocker) -> None:
    mocker.patch("miningcraft.protocol.connection.Connection")
    connection = make_connection(event_bus)

    connected = await connection.connect("localhost", 25565, "MiningBot")

    assert connected is True
    assert connection.is_connected is True
    event_bus.assert_published(EVENT_CONNECTED)


async def test_connect_failure(event_bus, mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.connection.Connection").return_value
    mock_conn.connect.side_effect = ConnectionRefusedError("connection refused")
    connection = make_connection(event_bus)

    connected = await connection.connect("localhost", 25565, "MiningBot")

    assert connected is False
    assert connection.is_connected is False
    assert EVENT_CONNECTED not in event_bus.event_names


async def test_connect_idempotent(event_bus, mocker) -> None:
    mocker.patch("miningcraft.protocol.connection.Connection")
    connection = make_connection(event_bus)

    assert await connection.connect("localhost", 25565, "MiningBot") is True
    assert await connection.connect("localhost", 25565, "MiningBot") is True

    assert len(event_bus.event_names) == 1
    await connection.disconnect()


async def test_disconnect(event_bus, mocker) -> None:
    mocker.patch("miningcraft.protocol.connection.Connection")
    connection = make_connection(event_bus)
    await connection.connect("localhost", 25565, "MiningBot")
    assert connection.is_connected is True

    await connection.disconnect()

    assert connection.is_connected is False
    event_bus.assert_published(EVENT_DISCONNECTED)


async def test_reconnect_success(event_bus, mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.connection.Connection").return_value
    mock_conn.connect.side_effect = [None, ConnectionRefusedError("down"), None]
    connection = make_connection(event_bus)

    assert await connection.connect("localhost", 25565, "MiningBot") is True
    await connection.disconnect()

    reconnected = await connection.reconnect()

    assert reconnected is True
    assert connection.is_connected is True
    assert mock_conn.connect.call_count == 3
    await connection.disconnect()


async def test_reconnect_exhausted(event_bus, mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.connection.Connection").return_value
    mock_conn.connect.side_effect = [
        None,
        ConnectionRefusedError("down"),
        ConnectionRefusedError("down"),
        ConnectionRefusedError("down"),
    ]
    connection = make_connection(event_bus)

    assert await connection.connect("localhost", 25565, "MiningBot") is True
    await connection.disconnect()

    reconnected = await connection.reconnect()

    assert reconnected is False
    assert connection.is_connected is False
    assert mock_conn.connect.call_count == 4


async def test_keepalive_monitors_incoming_packet(event_bus, mocker) -> None:
    """Receiving a keepalive refreshes the staleness timestamp.

    pyCraft answers keepalives itself; the connection's job is to observe them
    and tear down a stale connection (see ADR 012 note on keepalive handling).
    """
    mocker.patch("miningcraft.protocol.connection.Connection")
    connection = make_connection(event_bus, keepalive_interval=30.0, keepalive_timeout=120.0)
    await connection.connect("localhost", 25565, "MiningBot")

    packet = KeepAlivePacket()
    packet.keep_alive_id = 12345
    connection._on_keepalive_received(packet)

    assert connection._last_keepalive > 0
    await connection.disconnect()


async def test_keepalive_timeout_disconnects(event_bus, mocker) -> None:
    mocker.patch("miningcraft.protocol.connection.Connection")
    connection = make_connection(event_bus, keepalive_interval=0.001, keepalive_timeout=0.0)
    await connection.connect("localhost", 25565, "MiningBot")
    connection._last_keepalive = 0.0

    await connection._keepalive_loop()

    assert connection.is_connected is False
    event_bus.assert_published(EVENT_DISCONNECTED)
