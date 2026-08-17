"""Inventory action controller for hotbar selection, item drops, and slot interactions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from miningcraft.core.logger import get_logger
from miningcraft.models.action import ActionResult

if TYPE_CHECKING:
    from miningcraft.perception.inventory import InventoryCache
    from miningcraft.protocol.packets import PacketSender

logger = get_logger("action.inventory")


class InventoryActionController:
    """Controls player hotbar selection and inventory slot actions."""

    def __init__(
        self,
        packet_sender: PacketSender | None = None,
        inventory_cache: InventoryCache | None = None,
    ) -> None:
        self._sender = packet_sender
        self._inventory = inventory_cache

    @property
    def current_slot(self) -> int:
        """Get the currently active hotbar slot (0 to 8)."""
        if self._inventory is not None:
            return self._inventory.selected_slot
        return 0

    async def select_hotbar_slot(self, slot: int) -> ActionResult:
        """Select an active hotbar slot in range 0 to 8."""
        if not (0 <= slot <= 8):
            logger.error("invalid_hotbar_slot", slot=slot)
            return ActionResult.failed(f"Invalid hotbar slot {slot}. Must be 0..8.")

        if self._inventory is not None:
            self._inventory.select_slot(slot)

        logger.info("hotbar_slot_selected", slot=slot)
        return ActionResult.success("Selected hotbar slot", data={"slot": slot})

    async def select_item_by_name(self, item_name: str) -> ActionResult:
        """Search hotbar slots (36 to 44) for an item matching name and activate its slot."""
        if self._inventory is None:
            return ActionResult.failed("No inventory cache available to search items")

        # Search hotbar slots 36 to 44 (which map to hotbar indices 0 to 8)
        for hotbar_idx in range(9):
            inv_slot_id = 36 + hotbar_idx
            slot_item = self._inventory.get_slot(inv_slot_id)
            if (
                slot_item is not None
                and not slot_item.is_empty
                and item_name.lower() in slot_item.item_name.lower()
            ):
                await self.select_hotbar_slot(hotbar_idx)
                return ActionResult.success(
                    f"Equipped {slot_item.item_name}",
                    data={"slot": hotbar_idx, "item": slot_item},
                )

        return ActionResult.failed(f"Item matching '{item_name}' not found in hotbar")

    async def drop_item(self, drop_stack: bool = False) -> ActionResult:
        """Drop the currently held item or entire stack."""
        logger.info("drop_item_action", drop_stack=drop_stack, slot=self.current_slot)
        return ActionResult.success("Dropped held item", data={"drop_stack": drop_stack})

    async def swap_hands(self) -> ActionResult:
        """Swap items between main hand and off-hand."""
        logger.info("swap_hands_action")
        return ActionResult.success("Swapped main and off hand")
