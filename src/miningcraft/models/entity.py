"""Entity data models for tracking living mobs, players, and world objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miningcraft.models.position import Vec3

HOSTILE_ENTITIES = {
    "minecraft:zombie",
    "minecraft:skeleton",
    "minecraft:creeper",
    "minecraft:spider",
    "minecraft:cave_spider",
    "minecraft:witch",
    "minecraft:enderman",
    "minecraft:slime",
    "minecraft:drowned",
    "minecraft:husk",
    "minecraft:phantom",
}

PASSIVE_ENTITIES = {
    "minecraft:cow",
    "minecraft:sheep",
    "minecraft:pig",
    "minecraft:chicken",
    "minecraft:villager",
    "minecraft:horse",
    "minecraft:iron_golem",
}


@dataclass(slots=True)
class Entity:
    """Represents an active entity in the Minecraft world."""

    entity_id: int
    entity_type: str
    position: Vec3
    yaw: float = 0.0
    pitch: float = 0.0
    on_ground: bool = True
    custom_name: str | None = None
    is_alive: bool = True

    @property
    def is_hostile(self) -> bool:
        """Check if the entity is a hostile mob."""
        return self.entity_type in HOSTILE_ENTITIES

    @property
    def is_passive(self) -> bool:
        """Check if the entity is a passive or neutral animal."""
        return self.entity_type in PASSIVE_ENTITIES

    @property
    def is_player(self) -> bool:
        """Check if the entity is another player."""
        return self.entity_type == "minecraft:player"

    @property
    def is_item_drop(self) -> bool:
        """Check if the entity is a dropped item on the ground."""
        return self.entity_type == "minecraft:item"
