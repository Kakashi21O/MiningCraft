"""Tests for ActionManager facade."""

import pytest

from miningcraft.action.manager import ActionManager
from miningcraft.models.action import ActionStatus, BlockFace, Hand
from miningcraft.models.chunk import ChunkColumn
from miningcraft.models.inventory import InventorySlot
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.perception.cache import PerceptionManager


@pytest.mark.asyncio
async def test_action_manager_initialization_and_delegation() -> None:
    """ActionManager initializes sub-controllers and delegates commands correctly."""
    perception = PerceptionManager()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    perception.world.load_chunk(chunk)
    perception.world.set_block(BlockPos(0, 63, 0), state_id=1)
    perception.world.set_block(BlockPos(0, 64, 0), state_id=0)
    perception.player.update_position(x=0.0, y=64.0, z=0.0)

    action_mgr = ActionManager(perception=perception)

    # Test jump delegation
    res_jump = await action_mgr.jump()
    assert res_jump.status == ActionStatus.SUCCESS
    assert perception.player.state.position.y == 65.25

    # Test look_at delegation
    res_look = await action_mgr.look_at(Vec3(0.0, 64.0, 10.0))
    assert res_look.status == ActionStatus.SUCCESS
    assert perception.player.state.yaw == 0.0

    # Test mine_block delegation
    target_block = BlockPos(1, 64, 0)
    perception.world.set_block(target_block, state_id=1)
    res_mine = await action_mgr.mine_block(target_block, BlockFace.WEST)
    assert res_mine.status == ActionStatus.SUCCESS
    assert perception.world.get_block(target_block).id == 0

    # Test hotbar select
    perception.inventory.set_slot(
        36,
        InventorySlot(slot_id=36, item_id=278, item_name="minecraft:diamond_pickaxe", count=1),
    )
    res_tool = await action_mgr.select_tool("pickaxe")
    assert res_tool.status == ActionStatus.SUCCESS
    assert perception.inventory.selected_slot == 0

    # Test swing arm
    res_swing = await action_mgr.swing_arm(Hand.MAIN_HAND)
    assert res_swing.status == ActionStatus.SUCCESS
