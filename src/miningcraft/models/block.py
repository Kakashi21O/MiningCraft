"""Block data model representing world voxel units."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miningcraft.models.position import BlockPos

# Common hazardous block name patterns
HAZARD_BLOCKS = {
    "minecraft:lava",
    "minecraft:flowing_lava",
    "minecraft:fire",
    "minecraft:soul_fire",
    "minecraft:magma_block",
    "minecraft:sweet_berry_bush",
    "minecraft:wither_rose",
    "minecraft:powder_snow",
    "minecraft:cactus",
}

# Common fluid block names
FLUID_BLOCKS = {
    "minecraft:water",
    "minecraft:flowing_water",
    "minecraft:lava",
    "minecraft:flowing_lava",
}

# Common air block names
AIR_BLOCKS = {
    "minecraft:air",
    "minecraft:cave_air",
    "minecraft:void_air",
}


@dataclass(frozen=True, slots=True)
class Block:
    """Represents a discrete block in the Minecraft world."""

    id: int
    name: str
    position: BlockPos
    hardness: float = 1.0
    is_solid: bool = True
    is_fluid: bool = False
    is_transparent: bool = False
    state_id: int = 0

    @property
    def is_air(self) -> bool:
        """Check if this block is an air block."""
        return self.name in AIR_BLOCKS or self.id == 0

    @property
    def is_hazard(self) -> bool:
        """Check if this block is hazardous to the bot."""
        return self.name in HAZARD_BLOCKS

    @property
    def is_water(self) -> bool:
        """Check if this block is water or flowing water."""
        return self.name in ("minecraft:water", "minecraft:flowing_water")

    @property
    def is_lava(self) -> bool:
        """Check if this block is lava or flowing lava."""
        return self.name in ("minecraft:lava", "minecraft:flowing_lava")

    @property
    def is_ore(self) -> bool:
        """Check if this block is a mineable ore block."""
        return "ore" in self.name or self.name in (
            "minecraft:ancient_debris",
            "minecraft:raw_iron_block",
            "minecraft:raw_copper_block",
            "minecraft:raw_gold_block",
        )
