"""Tests for action data models."""

from miningcraft.models.action import (
    ActionResult,
    ActionStatus,
    BlockFace,
    DigRequest,
    DigStatus,
    Hand,
    LookTarget,
    MovementRequest,
    MovementType,
    PlaceBlockRequest,
)
from miningcraft.models.position import BlockPos, Vec3


def test_action_result_factories() -> None:
    """ActionResult factory methods set appropriate status and flags."""
    success = ActionResult.success(message="done", data={"x": 1})
    assert success.status == ActionStatus.SUCCESS
    assert success.is_success is True
    assert success.message == "done"
    assert success.data == {"x": 1}

    failed = ActionResult.failed(message="error")
    assert failed.status == ActionStatus.FAILED
    assert failed.is_success is False

    blocked = ActionResult.blocked(message="lava ahead")
    assert blocked.status == ActionStatus.BLOCKED
    assert blocked.is_success is False

    cancelled = ActionResult.cancelled(message="aborted")
    assert cancelled.status == ActionStatus.CANCELLED
    assert cancelled.is_success is False


def test_block_face_offsets() -> None:
    """BlockFace calculates correct relative BlockPos offsets."""
    assert BlockFace.BOTTOM.offset == BlockPos(0, -1, 0)
    assert BlockFace.TOP.offset == BlockPos(0, 1, 0)
    assert BlockFace.NORTH.offset == BlockPos(0, 0, -1)
    assert BlockFace.SOUTH.offset == BlockPos(0, 0, 1)
    assert BlockFace.WEST.offset == BlockPos(-1, 0, 0)
    assert BlockFace.EAST.offset == BlockPos(1, 0, 0)


def test_action_request_models() -> None:
    """Request data models initialize correctly with defaults and custom values."""
    move_req = MovementRequest(target=Vec3(10.0, 64.0, -5.0), movement_type=MovementType.SPRINT)
    assert move_req.target == Vec3(10.0, 64.0, -5.0)
    assert move_req.movement_type == MovementType.SPRINT
    assert move_req.tolerance == 0.3

    look_req = LookTarget(yaw=90.0, pitch=0.0)
    assert look_req.yaw == 90.0
    assert look_req.target_pos is None

    dig_req = DigRequest(position=BlockPos(1, 2, 3), face=BlockFace.NORTH)
    assert dig_req.position == BlockPos(1, 2, 3)
    assert dig_req.face == BlockFace.NORTH

    place_req = PlaceBlockRequest(
        position=BlockPos(1, 2, 3), face=BlockFace.TOP, hand=Hand.OFF_HAND
    )
    assert place_req.face == BlockFace.TOP
    assert place_req.hand == Hand.OFF_HAND
    assert place_req.cursor_x == 0.5
    assert DigStatus.START == 0
