"""Tests for MovementController and look angle calculations."""

import pytest

from miningcraft.action.movement import MovementController, calculate_look_angles
from miningcraft.action.safety import SafetyChecker
from miningcraft.models.action import ActionStatus
from miningcraft.models.chunk import ChunkColumn
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.perception.player import PlayerStateCache
from miningcraft.perception.world import WorldCache


def test_calculate_look_angles() -> None:
    """Calculates accurate Minecraft yaw and pitch."""
    pos = Vec3(0.0, 64.0, 0.0)

    # Directly South (+Z) -> yaw 0
    yaw_s, pitch_s = calculate_look_angles(pos, Vec3(0.0, 64.0 + 1.62, 10.0))
    assert yaw_s == 0.0
    assert pitch_s == 0.0

    # Directly North (-Z) -> yaw 180
    yaw_n, _ = calculate_look_angles(pos, Vec3(0.0, 64.0 + 1.62, -10.0))
    assert yaw_n == 180.0

    # Looking straight down -> pitch 90
    _, pitch_d = calculate_look_angles(pos, Vec3(0.0, 50.0, 0.0))
    assert pitch_d == 90.0

    # Looking straight up -> pitch -90
    _, pitch_u = calculate_look_angles(pos, Vec3(0.0, 80.0, 0.0))
    assert pitch_u == -90.0


@pytest.mark.asyncio
async def test_movement_controller_look_at() -> None:
    """MovementController updates look angles in player cache."""
    player_cache = PlayerStateCache()
    player_cache.update_position(x=0.0, y=64.0, z=0.0, yaw=0.0, pitch=0.0)

    controller = MovementController(player_cache=player_cache)
    res = await controller.look_at(Vec3(0.0, 64.0 + 1.62, -10.0))

    assert res.status == ActionStatus.SUCCESS
    assert player_cache.state.yaw == 180.0
    assert player_cache.state.pitch == 0.0


@pytest.mark.asyncio
async def test_movement_controller_walk_to() -> None:
    """MovementController steps incrementally towards destination."""
    player_cache = PlayerStateCache()
    player_cache.update_position(x=0.0, y=64.0, z=0.0)

    controller = MovementController(player_cache=player_cache, step_size=0.5)
    target = Vec3(2.0, 64.0, 0.0)

    res = await controller.walk_to(target, tolerance=0.1)
    assert res.status == ActionStatus.SUCCESS
    assert player_cache.state.position.distance(target) <= 0.1


@pytest.mark.asyncio
async def test_movement_controller_blocked_by_safety() -> None:
    """MovementController halts when step is blocked by safety checks."""
    player_cache = PlayerStateCache()
    player_cache.update_position(x=0.0, y=64.0, z=0.0)

    world = WorldCache()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    world.load_chunk(chunk)
    # Set lava at destination
    world.set_block(BlockPos(1, 64, 0), state_id=15)

    safety = SafetyChecker(world)
    controller = MovementController(player_cache=player_cache, safety_checker=safety, step_size=1.0)

    res = await controller.walk_to(Vec3(2.0, 64.0, 0.0))
    assert res.status == ActionStatus.BLOCKED
    assert "Dangerous liquid" in res.message


@pytest.mark.asyncio
async def test_movement_controller_jump() -> None:
    """MovementController performs jump and raises Y position."""
    player_cache = PlayerStateCache()
    player_cache.update_position(x=0.0, y=64.0, z=0.0)

    controller = MovementController(player_cache=player_cache)
    res = await controller.jump()

    assert res.status == ActionStatus.SUCCESS
    assert player_cache.state.position.y == 65.25
    assert player_cache.state.on_ground is False
