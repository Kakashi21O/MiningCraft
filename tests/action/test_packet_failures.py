"""Tests for packet send failures and action error handling."""

from unittest.mock import AsyncMock

import pytest

from miningcraft.action.inventory import InventoryActionController
from miningcraft.action.mining import MiningController
from miningcraft.action.movement import MovementController
from miningcraft.models.action import ActionStatus, BlockFace, Hand
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.protocol.packets import PacketSender


@pytest.mark.asyncio
async def test_movement_controller_sender_failure() -> None:
    """MovementController returns failed ActionResult when PacketSender fails."""
    mock_sender = AsyncMock(spec=PacketSender)
    mock_sender.send.return_value = False

    controller = MovementController(packet_sender=mock_sender)
    res = await controller.send_position_and_look(Vec3(1.0, 64.0, 1.0), yaw=0.0, pitch=0.0)

    assert res.status == ActionStatus.FAILED
    assert "Failed to send PositionAndLook" in res.message


@pytest.mark.asyncio
async def test_mining_controller_sender_failure() -> None:
    """MiningController returns failed ActionResult when swing arm packet fails."""
    mock_sender = AsyncMock(spec=PacketSender)
    mock_sender.send.return_value = False

    controller = MiningController(packet_sender=mock_sender)
    res = await controller.swing_arm(Hand.MAIN_HAND)

    assert res.status == ActionStatus.FAILED
    assert "Failed to send arm animation" in res.message

    res_place = await controller.place_block(BlockPos(0, 64, 0), face=BlockFace.TOP)
    assert res_place.status == ActionStatus.FAILED


@pytest.mark.asyncio
async def test_movement_controller_sprint_and_sneak_toggles() -> None:
    """MovementController correctly tracks sprint and sneak modes."""
    controller = MovementController()
    controller.set_sprinting(True)
    assert controller._is_sprinting is True
    controller.set_sprinting(False)
    assert controller._is_sprinting is False

    controller.set_sneaking(True)
    assert controller._is_sneaking is True
    controller.set_sneaking(False)
    assert controller._is_sneaking is False


@pytest.mark.asyncio
async def test_inventory_controller_drop_and_swap() -> None:
    """InventoryActionController executes drop and swap helpers."""
    controller = InventoryActionController()
    res_drop = await controller.drop_item(drop_stack=True)
    assert res_drop.status == ActionStatus.SUCCESS

    res_swap = await controller.swap_hands()
    assert res_swap.status == ActionStatus.SUCCESS
