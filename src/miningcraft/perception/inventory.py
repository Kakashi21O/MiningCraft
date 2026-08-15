"""Inventory cache tracking player slots, tools, and item counts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from miningcraft.core.logger import get_logger
from miningcraft.models.inventory import InventorySlot, InventoryState

if TYPE_CHECKING:
    pass

logger = get_logger("perception.inventory")


class InventoryCache:
    """In-memory tracking of the player inventory and hotbar state."""

    def __init__(self) -> None:
        self._state = InventoryState()

    @property
    def state(self) -> InventoryState:
        """Get underlying InventoryState."""
        return self._state

    @property
    def selected_slot(self) -> int:
        """Get the currently active hotbar slot ID."""
        return self._state.selected_slot

    def select_slot(self, slot_id: int) -> None:
        """Set the active hotbar slot ID."""
        self._state.selected_slot = slot_id

    def get_slot(self, slot_id: int) -> InventorySlot | None:
        """Get item in a specific inventory slot."""
        return self._state.get_slot(slot_id)

    def set_slot(self, slot_id: int, item: InventorySlot | None) -> None:
        """Update or clear an item slot."""
        self._state.set_slot(slot_id, item)

    def get_held_item(self) -> InventorySlot | None:
        """Get item held in the current hotbar selection."""
        return self._state.get_held_item()

    def find_items(self, item_name: str) -> list[InventorySlot]:
        """Find all slots containing items matching the specified name."""
        return self._state.find_items(item_name)

    def total_count(self, item_name: str) -> int:
        """Count the total quantity of an item across the entire inventory."""
        return self._state.total_count(item_name)

    def is_full(self, total_slots: int = 36) -> bool:
        """Check if main inventory and hotbar are full."""
        return self._state.is_full(total_slots)

    def empty_slots_count(self, total_slots: int = 36) -> int:
        """Return number of empty slots in the main player inventory."""
        occupied = sum(
            1
            for slot_id, slot in self._state.slots.items()
            if 9 <= slot_id <= 44 and not slot.is_empty
        )
        return max(0, total_slots - occupied)

    def clear(self) -> None:
        """Clear all inventory slots."""
        self._state.slots.clear()
