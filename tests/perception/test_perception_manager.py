"""Unit tests for PerceptionManager event subscriptions and coordination."""

from miningcraft.core.events import EventBus
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.perception.cache import PerceptionManager


def test_perception_manager_event_wiring() -> None:
    bus = EventBus()
    manager = PerceptionManager()
    manager.attach(bus)

    # 1. Player position update
    bus.publish("OnPlayerPositionUpdate", x=12.5, y=65.0, z=-20.5, yaw=180.0, pitch=0.0)
    assert manager.player.position == Vec3(12.5, 65.0, -20.5)
    assert manager.player.yaw == 180.0

    # 2. Block change update
    bus.publish("OnBlockChange", x=10, y=60, z=10, block_id=1)
    block = manager.world.get_block(BlockPos(10, 60, 10))
    assert block is not None
    assert block.id == 1

    # 3. Entity spawn update
    bus.publish(
        "OnEntitySpawn",
        entity_id=99,
        entity_type="minecraft:skeleton",
        x=5.0,
        y=64.0,
        z=5.0,
    )
    assert manager.entities.count == 1
    skeleton = manager.entities.get_entity(99)
    assert skeleton is not None
    assert skeleton.is_hostile

    # 4. Entity despawn update
    bus.publish("OnEntityDespawn", entity_id=99)
    assert manager.entities.count == 0

    manager.detach()
