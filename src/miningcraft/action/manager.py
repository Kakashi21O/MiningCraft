"""Unified ActionManager facade orchestrating movement, mining, and inventory actions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from miningcraft.action.inventory import InventoryActionController
from miningcraft.action.mining import MiningController
from miningcraft.action.movement import MovementController
from miningcraft.action.safety import SafetyChecker, SafetyConfig
from miningcraft.core.logger import get_logger
from miningcraft.models.action import ActionResult, BlockFace, Hand
from miningcraft.models.position import BlockPos, Vec3

if TYPE_CHECKING:
    from miningcraft.perception.cache import PerceptionManager
    from miningcraft.protocol.packets import PacketSender

logger = get_logger("action.manager")


class ActionManager:
    """Central action execution coordinator providing a clean facade for all bot actions."""

    def __init__(
        self,
        packet_sender: PacketSender | None = None,
        perception: PerceptionManager | None = None,
        safety_config: SafetyConfig | None = None,
    ) -> None:
        self._sender = packet_sender
        self._perception = perception

        world_cache = perception.world if perception else None
        player_cache = perception.player if perception else None
        inv_cache = perception.inventory if perception else None

        self.safety = (
            SafetyChecker(
                world_cache=world_cache,
                config=safety_config or SafetyConfig(),
            )
            if world_cache is not None
            else None
        )

        self.movement = MovementController(
            packet_sender=packet_sender,
            player_cache=player_cache,
            safety_checker=self.safety,
        )

        self.mining = MiningController(
            packet_sender=packet_sender,
            world_cache=world_cache,
            movement=self.movement,
        )

        self.inventory = InventoryActionController(
            packet_sender=packet_sender,
            inventory_cache=inv_cache,
        )
        logger.info("ActionManager initialized")

    async def walk_to(self, target: Vec3, tolerance: float = 0.3) -> ActionResult:
        """Navigate step-by-step towards target coordinate."""
        return await self.movement.walk_to(target, tolerance=tolerance)

    async def look_at(self, target: Vec3) -> ActionResult:
        """Rotate camera towards target coordinate."""
        return await self.movement.look_at(target)

    async def jump(self) -> ActionResult:
        """Perform a standard vertical jump."""
        return await self.movement.jump()

    async def mine_block(
        self,
        pos: BlockPos,
        face: BlockFace = BlockFace.TOP,
    ) -> ActionResult:
        """Execute a full mining sequence on a target block."""
        return await self.mining.dig_block(pos, face)

    async def place_block(
        self,
        pos: BlockPos,
        face: BlockFace = BlockFace.TOP,
        hand: Hand = Hand.MAIN_HAND,
    ) -> ActionResult:
        """Place a block against a target block face."""
        return await self.mining.place_block(pos, face, hand)

    async def select_slot(self, slot: int) -> ActionResult:
        """Select an active hotbar slot index (0..8)."""
        return await self.inventory.select_hotbar_slot(slot)

    async def select_tool(self, tool_name: str) -> ActionResult:
        """Search and select an item by name in hotbar."""
        return await self.inventory.select_item_by_name(tool_name)

    async def swing_arm(self, hand: Hand = Hand.MAIN_HAND) -> ActionResult:
        """Swing the specified arm."""
        return await self.mining.swing_arm(hand)
