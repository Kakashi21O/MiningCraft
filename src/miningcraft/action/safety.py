"""Safety checks and hazard prevention for bot actions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from miningcraft.core.logger import get_logger
from miningcraft.models.action import ActionResult
from miningcraft.models.position import BlockPos, Vec3

if TYPE_CHECKING:
    from miningcraft.perception.world import WorldCache

logger = get_logger("action.safety")


@dataclass(frozen=True, slots=True)
class SafetyConfig:
    """Configurable safety thresholds."""

    max_fall_height: int = 3
    lava_check_radius: int = 2
    water_check_radius: int = 1
    void_y_threshold: int = -64


class SafetyChecker:
    """Validates player safety before executing physical movements and interactions."""

    def __init__(
        self,
        world_cache: WorldCache,
        config: SafetyConfig | None = None,
    ) -> None:
        self._world = world_cache
        self.config = config or SafetyConfig()

    def check_position_safety(self, target: Vec3 | BlockPos) -> ActionResult:
        """Validate if moving to or standing at a position is safe."""
        block_pos = target.to_block_pos() if isinstance(target, Vec3) else target

        # 1. Void check
        if block_pos.y <= self.config.void_y_threshold:
            logger.warning("void_hazard_detected", pos=str(block_pos))
            return ActionResult.blocked(f"Position {block_pos} is at or below void threshold")

        # 2. Obstruction check (head / body space blocked by solid blocks)
        obstructed, obs_reason = self.check_obstruction(block_pos)
        if obstructed:
            logger.warning("position_obstructed", pos=str(block_pos), reason=obs_reason)
            return ActionResult.blocked(obs_reason)

        # 3. Liquid / Hazard check
        is_liquid, liquid_type = self.check_liquid_hazard(block_pos)
        if is_liquid:
            logger.warning("liquid_hazard_detected", pos=str(block_pos), hazard=liquid_type)
            return ActionResult.blocked(f"Dangerous liquid ({liquid_type}) near {block_pos}")

        # 4. Fall hazard check
        is_fall, fall_dist = self.check_fall_hazard(block_pos)
        if is_fall:
            msg = (
                f"Fall hazard at {block_pos}: "
                f"fall distance {fall_dist} > {self.config.max_fall_height}"
            )
            return ActionResult.blocked(msg)

        return ActionResult.success("Position is safe")

    def is_standable(self, pos: BlockPos) -> bool:
        """Check if a position has solid ground beneath it and open space for body and head."""
        below_pos = pos.offset(0, -1, 0)
        below_block = self._world.get_block(below_pos)
        if below_block is None or not below_block.is_solid:
            return False

        feet_block = self._world.get_block(pos)
        head_block = self._world.get_block(pos.offset(0, 1, 0))

        feet_clear = feet_block is None or not feet_block.is_solid
        head_clear = head_block is None or not head_block.is_solid
        return feet_clear and head_clear

    def check_obstruction(self, pos: BlockPos) -> tuple[bool, str]:
        """Check if the 2-block tall space (feet and head) is occupied by solid blocks."""
        feet_block = self._world.get_block(pos)
        if feet_block is not None and feet_block.is_solid:
            return True, f"Feet position {pos} is blocked by solid block: {feet_block.name}"

        head_pos = pos.offset(0, 1, 0)
        head_block = self._world.get_block(head_pos)
        if head_block is not None and head_block.is_solid:
            return True, f"Head position {head_pos} is blocked by solid block: {head_block.name}"

        return False, ""

    def check_fall_hazard(self, pos: BlockPos) -> tuple[bool, int]:
        """Check if standing at pos would cause an unsafe fall.

        Returns (is_hazard, drop_distance).
        """
        # Look downwards until a solid block or void is encountered
        drop = 0
        current_y = pos.y - 1

        while current_y >= self.config.void_y_threshold:
            check_pos = BlockPos(pos.x, current_y, pos.z)
            block = self._world.get_block(check_pos)

            if block is None:
                # Chunk not loaded - cannot verify ground
                return True, drop + 1

            if block.is_fluid and "lava" in block.name.lower():
                return True, drop + 1

            if block.is_solid:
                if drop > self.config.max_fall_height:
                    return True, drop
                return False, drop

            drop += 1
            current_y -= 1

        # Reached void
        return True, drop

    def check_liquid_hazard(
        self,
        pos: BlockPos,
        radius: int | None = None,
    ) -> tuple[bool, str | None]:
        """Scan surrounding blocks for dangerous fluids (lava or direct water)."""
        check_radius = radius if radius is not None else self.config.lava_check_radius

        # Check feet and head for any fluid
        for dy in (0, 1):
            check_p = pos.offset(0, dy, 0)
            b = self._world.get_block(check_p)
            if b is not None and b.is_fluid:
                return True, b.name

        # Check radius for lava
        blocks = self._world.get_blocks_in_radius(pos, check_radius)
        for b in blocks:
            if b.is_fluid and "lava" in b.name.lower():
                return True, b.name

        return False, None
