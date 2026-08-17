"""Tests for MiningController and InventoryActionController."""

import pytest

from miningcraft.action.inventory import InventoryActionController
from miningcraft.action.mining import MiningController
from miningcraft.action.movement import MovementController
from miningcraft.models.action import ActionStatus, BlockFace, Hand
from miningcraft.models.chunk import ChunkColumn
from miningcraft.models.inventory import InventorySlot
from miningcraft.models.position import BlockPos
from miningcraft.perception.inventory import InventoryCache
from miningcraft.perception.player import PlayerStateCache
from miningcraft.perception.world import WorldCache


@pytest.mark.asyncio
async def test_mining_controller_full_dig_cycle() -> None:
    """MiningController starts and finishes digging, updating world cache to air."""
    world = WorldCache()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    world.load_chunk(chunk)
    pos = BlockPos(1, 64, 1)
    world.set_block(pos, state_id=1, name="minecraft:stone")

    player = PlayerStateCache()
    movement = MovementController(player_cache=player)
    controller = MiningController(world_cache=world, movement=movement)

    # Start digging
    res_start = await controller.start_digging(pos, BlockFace.NORTH)
    assert res_start.status == ActionStatus.SUCCESS
    assert controller.is_digging is True
    assert controller.current_target == pos

    # Finish digging
    res_finish = await controller.finish_digging(pos, BlockFace.NORTH)
    assert res_finish.status == ActionStatus.SUCCESS
    assert controller.is_digging is False
    assert controller.current_target is None

    # Verify block in world cache changed to air (id 0)
    block_after = world.get_block(pos)
    assert block_after is not None
    assert block_after.id == 0


@pytest.mark.asyncio
async def test_mining_controller_place_block() -> None:
    """MiningController calculates correct placed block target."""
    player = PlayerStateCache()
    movement = MovementController(player_cache=player)
    controller = MiningController(movement=movement)

    pos = BlockPos(5, 60, 5)
    res = await controller.place_block(pos, face=BlockFace.TOP, hand=Hand.MAIN_HAND)

    assert res.status == ActionStatus.SUCCESS
    assert res.data["placed_pos"] == BlockPos(5, 61, 5)


@pytest.mark.asyncio
async def test_inventory_action_controller_selection() -> None:
    """InventoryActionController selects valid hotbar slots and rejects out-of-range slots."""
    inv_cache = InventoryCache()
    controller = InventoryActionController(inventory_cache=inv_cache)

    res_ok = await controller.select_hotbar_slot(3)
    assert res_ok.status == ActionStatus.SUCCESS
    assert inv_cache.selected_slot == 3

    res_invalid = await controller.select_hotbar_slot(12)
    assert res_invalid.status == ActionStatus.FAILED


@pytest.mark.asyncio
async def test_inventory_action_select_item_by_name() -> None:
    """InventoryActionController finds and selects items in hotbar."""
    inv_cache = InventoryCache()
    inv_cache.set_slot(
        38,
        InventorySlot(
            slot_id=38,
            item_id=278,
            item_name="minecraft:diamond_pickaxe",
            count=1,
        ),
    )

    controller = InventoryActionController(inventory_cache=inv_cache)
    res = await controller.select_item_by_name("diamond_pickaxe")

    assert res.status == ActionStatus.SUCCESS
    assert res.data["slot"] == 2
    assert inv_cache.selected_slot == 2

    # Not found search
    res_missing = await controller.select_item_by_name("netherite_sword")
    assert res_missing.status == ActionStatus.FAILED
