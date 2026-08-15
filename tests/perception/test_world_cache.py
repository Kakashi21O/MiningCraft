"""Unit tests for WorldCache."""

from miningcraft.models.chunk import ChunkColumn
from miningcraft.models.position import BlockPos
from miningcraft.perception.world import WorldCache


def test_world_cache_load_and_unload() -> None:
    cache = WorldCache()
    assert cache.loaded_chunks_count == 0

    chunk = ChunkColumn(chunk_x=0, chunk_z=0)
    cache.load_chunk(chunk)
    assert cache.loaded_chunks_count == 1
    assert cache.is_chunk_loaded(0, 0)
    assert not cache.is_chunk_loaded(1, 0)

    cache.unload_chunk(0, 0)
    assert cache.loaded_chunks_count == 0
    assert not cache.is_chunk_loaded(0, 0)


def test_world_cache_get_and_set_block() -> None:
    cache = WorldCache()
    pos = BlockPos(5, 64, 5)

    assert cache.get_block(pos) is None

    cache.set_block(pos, state_id=22, name="minecraft:diamond_ore")
    block = cache.get_block(pos)
    assert block is not None
    assert block.id == 22
    assert block.name == "minecraft:diamond_ore"
    assert block.is_ore


def test_world_cache_radius_queries() -> None:
    cache = WorldCache()
    center = BlockPos(0, 64, 0)

    cache.set_block(center, state_id=1, name="minecraft:stone")
    cache.set_block(center.east(), state_id=22, name="minecraft:diamond_ore")
    cache.set_block(center.up(), state_id=15, name="minecraft:lava")

    ores = cache.find_blocks(center, radius=2, predicate=lambda b: b.is_ore)
    assert len(ores) == 1
    assert ores[0].name == "minecraft:diamond_ore"

    hazards = cache.find_blocks(center, radius=2, predicate=lambda b: b.is_hazard)
    assert len(hazards) == 1
    assert hazards[0].is_lava

    nearest_ore = cache.find_nearest_block(center, radius=2, predicate=lambda b: b.is_ore)
    assert nearest_ore is not None
    assert nearest_ore.position == center.east()
