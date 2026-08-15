"""World state cache managing chunk columns and voxel block queries."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from miningcraft.core.logger import get_logger
from miningcraft.models.block import Block
from miningcraft.models.chunk import ChunkColumn

if TYPE_CHECKING:
    from miningcraft.models.position import BlockPos

logger = get_logger("perception.world")


class WorldCache:
    """In-memory cache of loaded Minecraft world chunks and voxel data."""

    def __init__(self) -> None:
        self._chunks: dict[tuple[int, int], ChunkColumn] = {}
        # Simple name lookup for basic standard block states
        self._block_names: dict[int, str] = {
            0: "minecraft:air",
            1: "minecraft:stone",
            2: "minecraft:granite",
            3: "minecraft:polished_granite",
            4: "minecraft:diorite",
            5: "minecraft:polished_diorite",
            6: "minecraft:andesite",
            7: "minecraft:polished_andesite",
            8: "minecraft:grass_block",
            9: "minecraft:dirt",
            10: "minecraft:coarse_dirt",
            11: "minecraft:cobblestone",
            12: "minecraft:bedrock",
            13: "minecraft:water",
            14: "minecraft:flowing_water",
            15: "minecraft:lava",
            16: "minecraft:flowing_lava",
            17: "minecraft:sand",
            18: "minecraft:gravel",
            19: "minecraft:gold_ore",
            20: "minecraft:iron_ore",
            21: "minecraft:coal_ore",
            22: "minecraft:diamond_ore",
            23: "minecraft:copper_ore",
            24: "minecraft:lapis_ore",
            25: "minecraft:redstone_ore",
            26: "minecraft:emerald_ore",
        }

    def register_block_name(self, block_id: int, name: str) -> None:
        """Register or override a friendly name for a block ID."""
        self._block_names[block_id] = name

    def is_chunk_loaded(self, chunk_x: int, chunk_z: int) -> bool:
        """Check if a chunk column is loaded in the cache."""
        return (chunk_x, chunk_z) in self._chunks

    def get_chunk(self, chunk_x: int, chunk_z: int) -> ChunkColumn | None:
        """Retrieve a loaded chunk column or None if not loaded."""
        return self._chunks.get((chunk_x, chunk_z))

    def load_chunk(self, chunk: ChunkColumn) -> None:
        """Add or replace a chunk column in the cache."""
        self._chunks[(chunk.chunk_x, chunk.chunk_z)] = chunk
        logger.debug("Chunk loaded into world cache", chunk_x=chunk.chunk_x, chunk_z=chunk.chunk_z)

    def unload_chunk(self, chunk_x: int, chunk_z: int) -> None:
        """Remove an unloaded chunk column from cache."""
        if (chunk_x, chunk_z) in self._chunks:
            del self._chunks[(chunk_x, chunk_z)]
            logger.debug(
                "Chunk unloaded from world cache",
                chunk_x=chunk_x,
                chunk_z=chunk_z,
            )

    def is_block_loaded(self, pos: BlockPos) -> bool:
        """Check if the chunk containing this block is currently loaded."""
        return self.is_chunk_loaded(pos.chunk_x, pos.chunk_z)

    def get_block(self, pos: BlockPos) -> Block | None:
        """Retrieve a Block at a given 3D position if the chunk is loaded."""
        chunk = self.get_chunk(pos.chunk_x, pos.chunk_z)
        if chunk is None:
            return None
        state_id = chunk.get_block_state(pos)
        name = self._block_names.get(state_id, f"minecraft:block_{state_id}")
        is_solid = state_id not in (0, 13, 14, 15, 16)
        is_fluid = state_id in (13, 14, 15, 16)
        return Block(
            id=state_id,
            name=name,
            position=pos,
            hardness=1.0,
            is_solid=is_solid,
            is_fluid=is_fluid,
            state_id=state_id,
        )

    def set_block(self, pos: BlockPos, state_id: int, name: str | None = None) -> None:
        """Update a single block state in the world cache."""
        chunk = self.get_chunk(pos.chunk_x, pos.chunk_z)
        if chunk is None:
            chunk = ChunkColumn(chunk_x=pos.chunk_x, chunk_z=pos.chunk_z)
            self.load_chunk(chunk)
        chunk.set_block_state(pos, state_id)
        if name is not None:
            self._block_names[state_id] = name

    def get_blocks_in_radius(self, center: BlockPos, radius: int) -> list[Block]:
        """Return all loaded blocks in a cubic radius around a center position."""
        blocks: list[Block] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                for dz in range(-radius, radius + 1):
                    pos = center.offset(dx, dy, dz)
                    block = self.get_block(pos)
                    if block is not None:
                        blocks.append(block)
        return blocks

    def find_blocks(
        self,
        center: BlockPos,
        radius: int,
        predicate: Callable[[Block], bool],
    ) -> list[Block]:
        """Search for all loaded blocks matching a condition within radius."""
        return [b for b in self.get_blocks_in_radius(center, radius) if predicate(b)]

    def find_nearest_block(
        self,
        center: BlockPos,
        radius: int,
        predicate: Callable[[Block], bool],
    ) -> Block | None:
        """Find the closest block matching a condition within radius."""
        matches = self.find_blocks(center, radius, predicate)
        if not matches:
            return None
        return min(matches, key=lambda b: b.position.distance_sq(center))

    @property
    def loaded_chunks_count(self) -> int:
        """Return number of loaded chunk columns."""
        return len(self._chunks)

    def clear(self) -> None:
        """Clear all loaded chunks from cache."""
        self._chunks.clear()
