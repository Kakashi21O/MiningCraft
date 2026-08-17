"""Player state cache maintaining real-time status of the bot."""

from __future__ import annotations

from typing import TYPE_CHECKING

from miningcraft.core.logger import get_logger
from miningcraft.models.player import PlayerState
from miningcraft.models.position import BlockPos, Vec3

if TYPE_CHECKING:
    pass

logger = get_logger("perception.player")


class PlayerStateCache:
    """In-memory cache of the bot's current physical and gameplay state."""

    def __init__(self, initial_position: Vec3 | None = None) -> None:
        pos = initial_position or Vec3(0.0, 0.0, 0.0)
        self._state = PlayerState(
            position=pos,
            yaw=0.0,
            pitch=0.0,
            on_ground=True,
            health=20.0,
            food=20,
            saturation=5.0,
            gamemode="survival",
            dimension="minecraft:overworld",
            is_alive=True,
        )

    @property
    def state(self) -> PlayerState:
        """Get the current PlayerState snapshot."""
        return self._state

    @property
    def position(self) -> Vec3:
        """Get current continuous position vector."""
        return self._state.position

    @property
    def block_position(self) -> BlockPos:
        """Get current integer block position."""
        return self._state.block_position

    @property
    def yaw(self) -> float:
        """Get current yaw rotation in degrees."""
        return self._state.yaw

    @property
    def pitch(self) -> float:
        """Get current pitch rotation in degrees."""
        return self._state.pitch

    @property
    def on_ground(self) -> bool:
        """Check if bot is currently standing on ground."""
        return self._state.on_ground

    @property
    def health(self) -> float:
        """Get current health points (0.0 - 20.0)."""
        return self._state.health

    @property
    def food(self) -> int:
        """Get current hunger level (0 - 20)."""
        return self._state.food

    @property
    def is_alive(self) -> bool:
        """Check if the bot is alive."""
        return self._state.is_alive and self._state.health > 0.0

    def update_position(
        self,
        x: float,
        y: float,
        z: float,
        yaw: float | None = None,
        pitch: float | None = None,
        on_ground: bool | None = None,
    ) -> None:
        """Update bot coordinate position and optional rotation/ground state."""
        self._state.position = Vec3(x, y, z)
        if yaw is not None:
            self._state.yaw = yaw
        if pitch is not None:
            self._state.pitch = pitch
        if on_ground is not None:
            self._state.on_ground = on_ground

    def update_health_and_food(
        self,
        health: float | None = None,
        food: int | None = None,
        saturation: float | None = None,
    ) -> None:
        """Update health, food level, and saturation values."""
        if health is not None:
            self._state.health = max(0.0, min(20.0, health))
            self._state.is_alive = self._state.health > 0.0
        if food is not None:
            self._state.food = max(0, min(20, food))
        if saturation is not None:
            self._state.saturation = max(0.0, saturation)

    def set_gamemode(self, gamemode: str) -> None:
        """Update current gamemode."""
        self._state.gamemode = gamemode

    def set_dimension(self, dimension: str) -> None:
        """Update current dimension identifier."""
        self._state.dimension = dimension
