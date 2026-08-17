"""Chunk and Section data models representing 16x16x16 and 16xHx16 voxel columns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from miningcraft.models.position import BlockPos

# Dimensions of a standard Minecraft chunk section
SECTION_WIDTH = 16
SECTION_HEIGHT = 16
SECTION_LENGTH = 16
SECTION_VOLUME = SECTION_WIDTH * SECTION_HEIGHT * SECTION_LENGTH


@dataclass(slots=True)
class ChunkSection:
    """Represents a 16x16x16 cubic section of blocks inside a chunk column."""

    y_index: int
    blocks: list[int] = field(default_factory=lambda: [0] * SECTION_VOLUME)

    @staticmethod
    def _index(x: int, y: int, z: int) -> int:
        """Convert local (x, y, z) 0-15 coordinates to linear array index (y * 256 + z * 16 + x)."""
        return (y & 15) * 256 + (z & 15) * 16 + (x & 15)

    def get_block_state(self, x: int, y: int, z: int) -> int:
        """Get the block state ID at local coordinates (0-15)."""
        return self.blocks[self._index(x, y, z)]

    def set_block_state(self, x: int, y: int, z: int, state_id: int) -> None:
        """Set the block state ID at local coordinates (0-15)."""
        self.blocks[self._index(x, y, z)] = state_id

    @property
    def is_empty(self) -> bool:
        """Check if this entire section is composed of air (all 0s)."""
        return all(b == 0 for b in self.blocks)


@dataclass(slots=True)
class ChunkColumn:
    """Represents a full vertical column of chunk sections at (chunk_x, chunk_z)."""

    chunk_x: int
    chunk_z: int
    sections: dict[int, ChunkSection] = field(default_factory=dict)
    is_loaded: bool = True

    def get_section(self, section_y: int, create_if_missing: bool = False) -> ChunkSection | None:
        """Retrieve a 16x16x16 section by Y section index."""
        if section_y in self.sections:
            return self.sections[section_y]
        if create_if_missing:
            section = ChunkSection(y_index=section_y)
            self.sections[section_y] = section
            return section
        return None

    def get_block_state(self, pos: BlockPos) -> int:
        """Retrieve the raw block state ID at the given world BlockPos."""
        section = self.get_section(pos.section_y)
        if section is None:
            return 0  # Air default
        return section.get_block_state(pos.local_x, pos.local_y, pos.local_z)

    def set_block_state(self, pos: BlockPos, state_id: int) -> None:
        """Update the block state ID at the given world BlockPos."""
        section = self.get_section(pos.section_y, create_if_missing=True)
        assert section is not None
        section.set_block_state(pos.local_x, pos.local_y, pos.local_z, state_id)
