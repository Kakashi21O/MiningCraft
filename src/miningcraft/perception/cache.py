"""Central perception manager combining world, player, entity, and inventory caches."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from miningcraft.core.logger import get_logger
from miningcraft.models.entity import Entity
from miningcraft.models.position import BlockPos, Vec3
from miningcraft.perception.entities import EntityCache
from miningcraft.perception.inventory import InventoryCache
from miningcraft.perception.player import PlayerStateCache
from miningcraft.perception.world import WorldCache

if TYPE_CHECKING:
    from miningcraft.core.events import EventBus

logger = get_logger("perception.manager")


class PerceptionManager:
    """Central perception coordinator wiring all state caches to the EventBus."""

    def __init__(
        self,
        world_cache: WorldCache | None = None,
        player_cache: PlayerStateCache | None = None,
        entity_cache: EntityCache | None = None,
        inventory_cache: InventoryCache | None = None,
    ) -> None:
        self.world = world_cache or WorldCache()
        self.player = player_cache or PlayerStateCache()
        self.entities = entity_cache or EntityCache()
        self.inventory = inventory_cache or InventoryCache()
        self._bus: EventBus | None = None

    def attach(self, event_bus: EventBus) -> None:
        """Subscribe cache update handlers to Core EventBus events."""
        self._bus = event_bus
        event_bus.subscribe("OnPlayerPositionUpdate", self._on_player_position)
        event_bus.subscribe("OnBlockChange", self._on_block_change)
        event_bus.subscribe("OnEntitySpawn", self._on_entity_spawn)
        event_bus.subscribe("OnEntityDespawn", self._on_entity_despawn)
        logger.info("PerceptionManager attached to EventBus")

    def detach(self) -> None:
        """Unsubscribe handlers from EventBus."""
        if self._bus is not None:
            self._bus.unsubscribe("OnPlayerPositionUpdate", self._on_player_position)
            self._bus.unsubscribe("OnBlockChange", self._on_block_change)
            self._bus.unsubscribe("OnEntitySpawn", self._on_entity_spawn)
            self._bus.unsubscribe("OnEntityDespawn", self._on_entity_despawn)
            self._bus = None
            logger.info("PerceptionManager detached from EventBus")

    def _on_player_position(self, event_type: str, **kwargs: Any) -> None:
        """Handle incoming player position and look updates."""
        x = kwargs.get("x")
        y = kwargs.get("y")
        z = kwargs.get("z")
        if x is not None and y is not None and z is not None:
            self.player.update_position(
                x=float(x),
                y=float(y),
                z=float(z),
                yaw=float(kwargs["yaw"]) if "yaw" in kwargs else None,
                pitch=float(kwargs["pitch"]) if "pitch" in kwargs else None,
                on_ground=bool(kwargs["on_ground"]) if "on_ground" in kwargs else None,
            )

    def _on_block_change(self, event_type: str, **kwargs: Any) -> None:
        """Handle incoming discrete block state modifications."""
        x = kwargs.get("x")
        y = kwargs.get("y")
        z = kwargs.get("z")
        block_id = kwargs.get("block_id") or kwargs.get("state_id")
        if x is not None and y is not None and z is not None and block_id is not None:
            pos = BlockPos(int(x), int(y), int(z))
            self.world.set_block(pos, int(block_id))

    def _on_entity_spawn(self, event_type: str, **kwargs: Any) -> None:
        """Handle newly spawned entities in the world."""
        entity_id = kwargs.get("entity_id")
        entity_type = kwargs.get("entity_type", "minecraft:unknown")
        x = kwargs.get("x", 0.0)
        y = kwargs.get("y", 0.0)
        z = kwargs.get("z", 0.0)
        if entity_id is not None:
            entity = Entity(
                entity_id=int(entity_id),
                entity_type=str(entity_type),
                position=Vec3(float(x), float(y), float(z)),
                yaw=float(kwargs.get("yaw", 0.0)),
                pitch=float(kwargs.get("pitch", 0.0)),
            )
            self.entities.add_entity(entity)

    def _on_entity_despawn(self, event_type: str, **kwargs: Any) -> None:
        """Handle despawned or destroyed entities."""
        entity_id = kwargs.get("entity_id")
        if entity_id is not None:
            self.entities.remove_entity(int(entity_id))

    def clear(self) -> None:
        """Reset all internal cache stores."""
        self.world.clear()
        self.entities.clear()
        self.inventory.clear()
