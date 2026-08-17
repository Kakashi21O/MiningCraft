"""Tests for vector mathematics edge cases."""

from miningcraft.models.position import Vec3


def test_vec3_length_and_normalize() -> None:
    """Vec3 calculates magnitude and unit direction correctly."""
    v = Vec3(3.0, 4.0, 0.0)
    assert v.length() == 5.0

    unit = v.normalize()
    assert unit.length() == 1.0
    assert unit.x == 0.6
    assert unit.y == 0.8
    assert unit.z == 0.0

    # Zero vector normalize returns (0, 0, 0)
    zero_unit = Vec3(0.0, 0.0, 0.0).normalize()
    assert zero_unit == Vec3(0.0, 0.0, 0.0)


def test_vec3_arithmetic() -> None:
    """Vec3 addition, subtraction, scalar multiplication, and distance alias."""
    v1 = Vec3(10.0, 20.0, 30.0)
    v2 = Vec3(2.0, 5.0, 10.0)

    # Subtraction
    diff = v1.sub(v2)
    assert diff == Vec3(8.0, 15.0, 20.0)

    # Multiplication
    scaled = v2.mul(3.0)
    assert scaled == Vec3(6.0, 15.0, 30.0)

    # Addition with other Vec3
    added = v1.add(other=v2)
    assert added == Vec3(12.0, 25.0, 40.0)

    # Distance alias
    assert v1.distance(v2) == v1.distance_to(v2)
