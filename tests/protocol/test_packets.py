"""Unit tests for PacketSender and PacketReceiver wrappers."""

from minecraft.networking.packets.clientbound.play import KeepAlivePacket

from miningcraft.protocol.packets import PacketReceiver, PacketSender


def make_packet() -> KeepAlivePacket:
    packet = KeepAlivePacket()
    packet.keep_alive_id = 42
    return packet


async def test_send_returns_true_on_success(mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.packets.Connection").return_value
    sender = PacketSender(mock_conn)

    ok = await sender.send(make_packet())

    assert ok is True
    mock_conn.write_packet.assert_called_once()


async def test_send_returns_false_on_failure(mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.packets.Connection").return_value
    mock_conn.write_packet.side_effect = OSError("socket closed")
    sender = PacketSender(mock_conn)

    ok = await sender.send(make_packet())

    assert ok is False


def test_register_and_receive_listener(mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.packets.Connection").return_value
    receiver = PacketReceiver(mock_conn)
    received: list[KeepAlivePacket] = []
    receiver.register_listener(KeepAlivePacket, received.append)

    receiver._forward(make_packet())

    assert len(received) == 1
    assert received[0].keep_alive_id == 42
    mock_conn.register_packet_listener.assert_called_once()


def test_register_installs_single_hook_for_type(mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.packets.Connection").return_value
    receiver = PacketReceiver(mock_conn)

    receiver.register_listener(KeepAlivePacket, lambda packet: None)
    receiver.register_listener(KeepAlivePacket, lambda packet: None)

    assert mock_conn.register_packet_listener.call_count == 1


def test_remove_listener(mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.packets.Connection").return_value
    receiver = PacketReceiver(mock_conn)
    received: list[KeepAlivePacket] = []
    receiver.register_listener(KeepAlivePacket, received.append)

    receiver.remove_listener(KeepAlivePacket)
    receiver._forward(make_packet())

    assert received == []


def test_listener_removed_during_dispatch_does_not_break(mocker) -> None:
    mock_conn = mocker.patch("miningcraft.protocol.packets.Connection").return_value
    receiver = PacketReceiver(mock_conn)
    received: list[KeepAlivePacket] = []

    def self_removing(packet: KeepAlivePacket) -> None:
        receiver.remove_listener(KeepAlivePacket)

    def recording(packet: KeepAlivePacket) -> None:
        received.append(packet)

    receiver.register_listener(KeepAlivePacket, self_removing)
    receiver.register_listener(KeepAlivePacket, recording)

    receiver._forward(make_packet())

    assert len(received) == 1
