"""Player state data model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miningcraft.models.position import BlockPos, Vec3


@dataclass(slots=True)
class PlayerState:
    """Represents the real-time physical and gameplay state of the bot."""

    position: Vec3
    yaw: float = 0.0
    pitch: float = 0.0
    on_ground: bool = True
    health: float = 20.0
    food: int = 20
    saturation: float = 5.0
    gamemode: str = "survival"
    dimension: str = "minecraft:overworld"
    is_alive: bool = True

    @property
    def block_position(self) -> BlockPos:
        """Get integer block coordinate of current player position."""
        return self.position.to_block_pos()

    @property
    def is_low_health(self) -> bool:
        """Check if bot health is dangerously low (<= 6.0 / 3 hearts)."""
        return self.health <= 6.0

    @property
    def is_hungry(self) -> bool:
        """Check if bot hunger is low enough to require eating (<= 14 / 7 drumsticks)."""
        return self.food <= 14
