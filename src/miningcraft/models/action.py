"""Action request and result models for physical execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from typing import Any

from miningcraft.models.position import BlockPos, Vec3


class ActionStatus(StrEnum):
    """Execution status of an action."""

    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"


class BlockFace(IntEnum):
    """Directional faces of a block in Minecraft protocol order."""

    BOTTOM = 0  # -Y
    TOP = 1  # +Y
    NORTH = 2  # -Z
    SOUTH = 3  # +Z
    WEST = 4  # -X
    EAST = 5  # +X

    @property
    def offset(self) -> BlockPos:
        """Get the relative coordinate offset for this face."""
        offsets = {
            BlockFace.BOTTOM: BlockPos(0, -1, 0),
            BlockFace.TOP: BlockPos(0, 1, 0),
            BlockFace.NORTH: BlockPos(0, 0, -1),
            BlockFace.SOUTH: BlockPos(0, 0, 1),
            BlockFace.WEST: BlockPos(-1, 0, 0),
            BlockFace.EAST: BlockPos(1, 0, 0),
        }
        return offsets[self]


class DigStatus(IntEnum):
    """Digging action stages matching the Player Digging packet."""

    START = 0
    CANCEL = 1
    FINISH = 2
    DROP_STACK = 3
    DROP_ITEM = 4
    SHOOT_ARROW = 5


class Hand(IntEnum):
    """Player hand identifier."""

    MAIN_HAND = 0
    OFF_HAND = 1


class MovementType(StrEnum):
    """Type of locomotion."""

    WALK = "walk"
    SPRINT = "sprint"
    SNEAK = "sneak"
    JUMP = "jump"


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Outcome of an action execution."""

    status: ActionStatus
    message: str = ""
    data: Any = None

    @property
    def is_success(self) -> bool:
        """Return whether the action succeeded."""
        return self.status == ActionStatus.SUCCESS

    @classmethod
    def success(cls, message: str = "", data: Any = None) -> ActionResult:
        """Construct a successful action result."""
        return cls(status=ActionStatus.SUCCESS, message=message, data=data)

    @classmethod
    def failed(cls, message: str = "", data: Any = None) -> ActionResult:
        """Construct a failed action result."""
        return cls(status=ActionStatus.FAILED, message=message, data=data)

    @classmethod
    def blocked(cls, message: str = "", data: Any = None) -> ActionResult:
        """Construct a blocked action result."""
        return cls(status=ActionStatus.BLOCKED, message=message, data=data)

    @classmethod
    def cancelled(cls, message: str = "", data: Any = None) -> ActionResult:
        """Construct a cancelled action result."""
        return cls(status=ActionStatus.CANCELLED, message=message, data=data)


@dataclass(frozen=True, slots=True)
class LookTarget:
    """Target orientation or coordinate to face."""

    yaw: float | None = None
    pitch: float | None = None
    target_pos: Vec3 | None = None


@dataclass(frozen=True, slots=True)
class MovementRequest:
    """Request to navigate/move to a position."""

    target: Vec3
    movement_type: MovementType = MovementType.WALK
    tolerance: float = 0.3
    timeout: float = 10.0


@dataclass(frozen=True, slots=True)
class DigRequest:
    """Request to break a specific block."""

    position: BlockPos
    face: BlockFace = BlockFace.TOP


@dataclass(frozen=True, slots=True)
class PlaceBlockRequest:
    """Request to place a block against a target block face."""

    position: BlockPos
    face: BlockFace = BlockFace.TOP
    hand: Hand = Hand.MAIN_HAND
    cursor_x: float = 0.5
    cursor_y: float = 0.5
    cursor_z: float = 0.5
