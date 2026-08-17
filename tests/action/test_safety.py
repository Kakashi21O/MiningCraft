"""Tests for SafetyChecker."""

from miningcraft.action.safety import SafetyChecker, SafetyConfig
from miningcraft.models.action import ActionStatus
from miningcraft.models.chunk import ChunkColumn
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.perception.world import WorldCache


def test_safety_checker_standable_and_safe() -> None:
    """SafetyChecker recognizes safe standable position with ground beneath."""
    world = WorldCache()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    world.load_chunk(chunk)

    # Put stone at y=63, air at y=64 and y=65
    world.set_block(BlockPos(0, 63, 0), state_id=1)  # stone (solid)
    world.set_block(BlockPos(0, 64, 0), state_id=0)  # air
    world.set_block(BlockPos(0, 65, 0), state_id=0)  # air

    checker = SafetyChecker(world)
    pos = BlockPos(0, 64, 0)

    assert checker.is_standable(pos) is True
    res = checker.check_position_safety(pos)
    assert res.status == ActionStatus.SUCCESS
    assert res.is_success is True


def test_safety_checker_obstruction() -> None:
    """SafetyChecker detects solid blocks at feet or head."""
    world = WorldCache()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    world.load_chunk(chunk)

    world.set_block(BlockPos(0, 63, 0), state_id=1)  # ground
    world.set_block(BlockPos(0, 64, 0), state_id=1)  # blocked feet
    world.set_block(BlockPos(0, 65, 0), state_id=0)

    checker = SafetyChecker(world)
    pos = BlockPos(0, 64, 0)

    res = checker.check_position_safety(pos)
    assert res.status == ActionStatus.BLOCKED
    assert "Feet position" in res.message


def test_safety_checker_fall_hazard() -> None:
    """SafetyChecker blocks movements where fall distance exceeds threshold."""
    world = WorldCache()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    world.load_chunk(chunk)

    # Ground is 5 blocks below (drop of 5 > default max 3)
    world.set_block(BlockPos(0, 58, 0), state_id=1)
    for y in range(59, 66):
        world.set_block(BlockPos(0, y, 0), state_id=0)

    checker = SafetyChecker(world, SafetyConfig(max_fall_height=3))
    pos = BlockPos(0, 64, 0)

    is_hazard, drop = checker.check_fall_hazard(pos)
    assert is_hazard is True
    assert drop == 5

    res = checker.check_position_safety(pos)
    assert res.status == ActionStatus.BLOCKED
    assert "Fall hazard" in res.message


def test_safety_checker_lava_hazard() -> None:
    """SafetyChecker blocks movements near lava."""
    world = WorldCache()
    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    world.load_chunk(chunk)

    world.set_block(BlockPos(0, 63, 0), state_id=1)  # solid ground
    world.set_block(BlockPos(0, 64, 0), state_id=0)  # air
    world.set_block(BlockPos(0, 65, 0), state_id=0)  # air
    world.set_block(BlockPos(1, 64, 0), state_id=15)  # lava next to player

    checker = SafetyChecker(world)
    res = checker.check_position_safety(Vec3(0.0, 64.0, 0.0))
    assert res.status == ActionStatus.BLOCKED
    assert "Dangerous liquid" in res.message


def test_safety_checker_void_threshold() -> None:
    """SafetyChecker blocks positions below void threshold."""
    world = WorldCache()
    checker = SafetyChecker(world, SafetyConfig(void_y_threshold=-64))
    res = checker.check_position_safety(BlockPos(0, -65, 0))
    assert res.status == ActionStatus.BLOCKED
    assert "void threshold" in res.message
