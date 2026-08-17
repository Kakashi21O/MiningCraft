"""Unit tests for Block, ChunkSection, and ChunkColumn models."""

from miningcraft.models.block import Block
from miningcraft.models.chunk import ChunkColumn, ChunkSection
from miningcraft.models.position import BlockPos


def test_block_properties() -> None:
    air_block = Block(id=0, name="minecraft:air", position=BlockPos(0, 0, 0), is_solid=False)
    assert air_block.is_air
    assert not air_block.is_hazard
    assert not air_block.is_ore

    lava_block = Block(id=10, name="minecraft:lava", position=BlockPos(1, 10, 1), is_fluid=True)
    assert lava_block.is_lava
    assert lava_block.is_hazard
    assert not lava_block.is_air

    ore_block = Block(id=56, name="minecraft:diamond_ore", position=BlockPos(2, 12, 2))
    assert ore_block.is_ore
    assert not ore_block.is_hazard


def test_chunk_section() -> None:
    section = ChunkSection(y_index=4)
    assert section.is_empty
    section.set_block_state(2, 3, 4, 1)  # stone
    assert not section.is_empty
    assert section.get_block_state(2, 3, 4) == 1
    assert section.get_block_state(0, 0, 0) == 0


def test_chunk_column() -> None:
    column = ChunkColumn(chunk_x=1, chunk_z=2)
    pos = BlockPos(18, 65, 34)  # chunk_x=1, chunk_z=2, section_y=4
    assert column.get_block_state(pos) == 0

    column.set_block_state(pos, 56)  # diamond ore
    assert column.get_block_state(pos) == 56
    assert column.get_section(4) is not None
    assert column.get_section(5) is None
