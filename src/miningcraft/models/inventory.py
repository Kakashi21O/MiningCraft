"""Inventory slot and container state data models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InventorySlot:
    """Represents an individual item slot in an inventory."""

    slot_id: int
    item_id: int
    item_name: str
    count: int = 1
    durability: int | None = None
    max_durability: int | None = None

    @property
    def is_empty(self) -> bool:
        """Check if the slot holds no items."""
        return self.count <= 0 or self.item_id == 0 or self.item_name in ("", "minecraft:air")

    @property
    def is_tool(self) -> bool:
        """Check if this item is a damageable tool."""
        return self.max_durability is not None and self.max_durability > 0

    @property
    def is_damaged(self) -> bool:
        """Check if tool has taken damage."""
        if self.durability is None or self.max_durability is None:
            return False
        return self.durability < self.max_durability


@dataclass(slots=True)
class InventoryState:
    """Represents the player inventory storage and hotbar selection."""

    slots: dict[int, InventorySlot] = field(default_factory=dict)
    selected_slot: int = 36  # Hotbar index 0 defaults to slot ID 36 in Minecraft standard window

    def get_slot(self, slot_id: int) -> InventorySlot | None:
        """Retrieve the item at a specific slot ID."""
        return self.slots.get(slot_id)

    def set_slot(self, slot_id: int, item: InventorySlot | None) -> None:
        """Set or clear an inventory slot."""
        if item is None or item.is_empty:
            self.slots.pop(slot_id, None)
        else:
            self.slots[slot_id] = item

    def get_held_item(self) -> InventorySlot | None:
        """Get the item currently held in the active hotbar slot."""
        return self.slots.get(self.selected_slot)

    def find_items(self, item_name: str) -> list[InventorySlot]:
        """Find all slots containing items matching the specified name."""
        return [slot for slot in self.slots.values() if slot.item_name == item_name]

    def total_count(self, item_name: str) -> int:
        """Count the total quantity of an item across all inventory slots."""
        return sum(slot.count for slot in self.find_items(item_name))

    def is_full(self, total_slots: int = 36) -> bool:
        """Check if all main inventory and hotbar slots (default 36) are occupied."""
        # Non-empty items in main inventory range (slots 9 to 44 in player window)
        occupied = sum(
            1 for slot_id, slot in self.slots.items() if 9 <= slot_id <= 44 and not slot.is_empty
        )
        return occupied >= total_slots
