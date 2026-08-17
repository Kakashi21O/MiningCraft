"""Unit tests for PlayerStateCache and EntityCache."""

from miningcraft.models.entity import Entity
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.perception.entities import EntityCache
from miningcraft.perception.player import PlayerStateCache


def test_player_state_cache() -> None:
    cache = PlayerStateCache(Vec3(0.0, 64.0, 0.0))
    assert cache.position == Vec3(0.0, 64.0, 0.0)
    assert cache.block_position == BlockPos(0, 64, 0)
    assert cache.is_alive

    cache.update_position(10.5, 70.0, -5.2, yaw=90.0, pitch=15.0, on_ground=False)
    assert cache.position == Vec3(10.5, 70.0, -5.2)
    assert cache.yaw == 90.0
    assert not cache.on_ground

    cache.update_health_and_food(health=0.0, food=0)
    assert not cache.is_alive


def test_entity_cache() -> None:
    cache = EntityCache()
    zombie = Entity(entity_id=1, entity_type="minecraft:zombie", position=Vec3(0.0, 64.0, 0.0))
    cow = Entity(entity_id=2, entity_type="minecraft:cow", position=Vec3(10.0, 64.0, 0.0))

    cache.add_entity(zombie)
    cache.add_entity(cow)
    assert cache.count == 2
    assert cache.get_entity(1) == zombie

    hostiles = cache.get_hostile_entities_in_radius(Vec3(0.0, 64.0, 0.0), radius=5.0)
    assert len(hostiles) == 1
    assert hostiles[0].entity_id == 1

    nearest = cache.get_nearest_entity(Vec3(0.0, 64.0, 0.0), radius=15.0)
    assert nearest == zombie

    cache.remove_entity(1)
    assert cache.count == 1
    assert cache.get_entity(1) is None
