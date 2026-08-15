"""Unit tests for Vec3 and BlockPos coordinate models."""

from miningcraft.models.position import BlockPos, Vec3


def test_blockpos_chunk_coordinates() -> None:
    pos = BlockPos(x=35, y=68, z=-18)
    assert pos.chunk_x == 2
    assert pos.chunk_z == -2
    assert pos.section_y == 4
    assert pos.local_x == 3
    assert pos.local_y == 4
    assert pos.local_z == 14


def test_blockpos_offsets() -> None:
    pos = BlockPos(10, 64, 10)
    assert pos.up().y == 65
    assert pos.down().y == 63
    assert pos.north().z == 9
    assert pos.south().z == 11
    assert pos.west().x == 9
    assert pos.east().x == 11
    assert pos.offset(2, -3, 4) == BlockPos(12, 61, 14)


def test_blockpos_distances() -> None:
    p1 = BlockPos(0, 0, 0)
    p2 = BlockPos(3, 4, 0)
    assert p1.distance_sq(p2) == 25
    assert p1.distance_to(p2) == 5.0
    assert p1.manhattan_distance(p2) == 7


def test_vec3_operations() -> None:
    v1 = Vec3(1.2, 64.5, 3.8)
    v2 = v1.add(dx=0.8, dy=0.5, dz=-0.8)
    assert v2 == Vec3(2.0, 65.0, 3.0)
    assert v1.to_block_pos() == BlockPos(1, 64, 3)
    assert v1.distance_sq(Vec3(1.2, 64.5, 3.8)) == 0.0
    assert v1.to_tuple() == (1.2, 64.5, 3.8)
