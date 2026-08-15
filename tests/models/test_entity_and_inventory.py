"""Unit tests for Entity, PlayerState, and Inventory models."""

from miningcraft.models.entity import Entity
from miningcraft.models.inventory import InventorySlot, InventoryState
from miningcraft.models.player import PlayerState
from miningcraft.models.position import BlockPos, Vec3


def test_entity_model() -> None:
    zombie = Entity(entity_id=101, entity_type="minecraft:zombie", position=Vec3(10.0, 64.0, 10.0))
    assert zombie.is_hostile
    assert not zombie.is_passive
    assert not zombie.is_player
    assert not zombie.is_item_drop

    cow = Entity(entity_id=102, entity_type="minecraft:cow", position=Vec3(12.0, 64.0, 12.0))
    assert cow.is_passive
    assert not cow.is_hostile


def test_player_state_model() -> None:
    player = PlayerState(position=Vec3(5.5, 64.0, -10.2), health=5.0, food=10)
    assert player.block_position == BlockPos(5, 64, -11)
    assert player.is_low_health
    assert player.is_hungry
    assert player.is_alive


def test_inventory_models() -> None:
    inv = InventoryState()
    slot = InventorySlot(
        slot_id=36,
        item_id=278,
        item_name="minecraft:diamond_pickaxe",
        count=1,
        durability=1500,
        max_durability=1561,
    )
    assert slot.is_tool
    assert slot.is_damaged
    assert not slot.is_empty

    inv.set_slot(36, slot)
    assert inv.get_slot(36) == slot
    assert inv.get_held_item() == slot
    assert inv.total_count("minecraft:diamond_pickaxe") == 1
    assert not inv.is_full()
