"""Entity cache managing living and non-living world entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from miningcraft.core.logger import get_logger
from miningcraft.models.entity import Entity

if TYPE_CHECKING:
    from miningcraft.models.position import Vec3

logger = get_logger("perception.entities")


class EntityCache:
    """In-memory tracking of all visible nearby entities."""

    def __init__(self) -> None:
        self._entities: dict[int, Entity] = {}

    def add_entity(self, entity: Entity) -> None:
        """Add or update an entity in the cache."""
        self._entities[entity.entity_id] = entity
        logger.debug(
            "Entity added to cache",
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
        )

    def remove_entity(self, entity_id: int) -> Entity | None:
        """Remove a despawned or dead entity from the cache."""
        entity = self._entities.pop(entity_id, None)
        if entity:
            logger.debug(
                "Entity removed from cache",
                entity_id=entity_id,
                entity_type=entity.entity_type,
            )
        return entity

    def get_entity(self, entity_id: int) -> Entity | None:
        """Retrieve an entity by unique entity ID."""
        return self._entities.get(entity_id)

    def update_entity_position(
        self,
        entity_id: int,
        position: Vec3,
        yaw: float | None = None,
        pitch: float | None = None,
        on_ground: bool | None = None,
    ) -> None:
        """Update an existing entity's position and orientation."""
        entity = self.get_entity(entity_id)
        if entity is None:
            return
        entity.position = position
        if yaw is not None:
            entity.yaw = yaw
        if pitch is not None:
            entity.pitch = pitch
        if on_ground is not None:
            entity.on_ground = on_ground

    def get_all_entities(self) -> list[Entity]:
        """Return all currently tracked entities."""
        return list(self._entities.values())

    def get_entities_in_radius(
        self,
        center: Vec3,
        radius: float,
        entity_type: str | None = None,
    ) -> list[Entity]:
        """Get entities within radius of a point, optionally filtered by type."""
        radius_sq = radius * radius
        result: list[Entity] = []
        for entity in self._entities.values():
            if entity_type is not None and entity.entity_type != entity_type:
                continue
            if entity.position.distance_sq(center) <= radius_sq:
                result.append(entity)
        return result

    def get_hostile_entities_in_radius(self, center: Vec3, radius: float) -> list[Entity]:
        """Get all hostile monsters within distance of center."""
        radius_sq = radius * radius
        return [
            e
            for e in self._entities.values()
            if e.is_hostile and e.position.distance_sq(center) <= radius_sq
        ]

    def get_nearest_entity(
        self,
        center: Vec3,
        radius: float,
        entity_type: str | None = None,
    ) -> Entity | None:
        """Find the single closest entity to center within radius."""
        nearby = self.get_entities_in_radius(center, radius, entity_type)
        if not nearby:
            return None
        return min(nearby, key=lambda e: e.position.distance_sq(center))

    @property
    def count(self) -> int:
        """Return count of active tracked entities."""
        return len(self._entities)

    def clear(self) -> None:
        """Clear all entity tracking data."""
        self._entities.clear()
