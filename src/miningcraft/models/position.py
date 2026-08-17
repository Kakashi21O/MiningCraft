"""Position and vector models for 3D coordinate mathematics."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(frozen=True, slots=True)
class BlockPos:
    """Integer block coordinate in 3D Minecraft world space."""

    x: int
    y: int
    z: int

    @property
    def chunk_x(self) -> int:
        """Get the chunk X coordinate (floor division by 16)."""
        return self.x >> 4

    @property
    def chunk_z(self) -> int:
        """Get the chunk Z coordinate (floor division by 16)."""
        return self.z >> 4

    @property
    def section_y(self) -> int:
        """Get the chunk section Y index (floor division by 16)."""
        return self.y >> 4

    @property
    def local_x(self) -> int:
        """Get the relative coordinate (0-15) inside its chunk column."""
        return self.x & 15

    @property
    def local_y(self) -> int:
        """Get the relative coordinate (0-15) inside its chunk section."""
        return self.y & 15

    @property
    def local_z(self) -> int:
        """Get the relative coordinate (0-15) inside its chunk column."""
        return self.z & 15

    def offset(self, dx: int = 0, dy: int = 0, dz: int = 0) -> BlockPos:
        """Return a new BlockPos shifted by (dx, dy, dz)."""
        return BlockPos(self.x + dx, self.y + dy, self.z + dz)

    def up(self, n: int = 1) -> BlockPos:
        """Return a new BlockPos n blocks up."""
        return BlockPos(self.x, self.y + n, self.z)

    def down(self, n: int = 1) -> BlockPos:
        """Return a new BlockPos n blocks down."""
        return BlockPos(self.x, self.y - n, self.z)

    def north(self, n: int = 1) -> BlockPos:
        """Return a new BlockPos n blocks north (-Z)."""
        return BlockPos(self.x, self.y, self.z - n)

    def south(self, n: int = 1) -> BlockPos:
        """Return a new BlockPos n blocks south (+Z)."""
        return BlockPos(self.x, self.y, self.z + n)

    def west(self, n: int = 1) -> BlockPos:
        """Return a new BlockPos n blocks west (-X)."""
        return BlockPos(self.x - n, self.y, self.z)

    def east(self, n: int = 1) -> BlockPos:
        """Return a new BlockPos n blocks east (+X)."""
        return BlockPos(self.x + n, self.y, self.z)

    def distance_to(self, other: BlockPos) -> float:
        """Euclidean distance to another block position."""
        return math.sqrt(self.distance_sq(other))

    def distance_sq(self, other: BlockPos) -> int:
        """Squared Euclidean distance to another block position."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return dx * dx + dy * dy + dz * dz

    def manhattan_distance(self, other: BlockPos) -> int:
        """Manhattan distance (|dx| + |dy| + |dz|) to another block position."""
        return abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)

    def to_vec3(self) -> Vec3:
        """Convert block coordinate to continuous Vec3 (at block center)."""
        return Vec3(self.x + 0.5, float(self.y), self.z + 0.5)

    def to_tuple(self) -> tuple[int, int, int]:
        """Convert to (x, y, z) tuple."""
        return self.x, self.y, self.z


@dataclass(frozen=True, slots=True)
class Vec3:
    """Continuous 3D position vector in Minecraft world space."""

    x: float
    y: float
    z: float

    def distance(self, other: Vec3) -> float:
        """Alias for distance_to."""
        return self.distance_to(other)

    def distance_to(self, other: Vec3) -> float:
        """Euclidean distance to another vector."""
        return math.sqrt(self.distance_sq(other))

    def distance_sq(self, other: Vec3) -> float:
        """Squared Euclidean distance to another vector."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return dx * dx + dy * dy + dz * dz

    def length(self) -> float:
        """Euclidean length / magnitude of vector."""
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> Vec3:
        """Return unit vector pointing in same direction."""
        mag = self.length()
        if mag == 0:
            return Vec3(0.0, 0.0, 0.0)
        return Vec3(self.x / mag, self.y / mag, self.z / mag)

    def add(
        self,
        other: Vec3 | None = None,
        dx: float = 0.0,
        dy: float = 0.0,
        dz: float = 0.0,
    ) -> Vec3:
        """Return vector translated by either another Vec3 or delta coordinates."""
        if other is not None:
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        return Vec3(self.x + dx, self.y + dy, self.z + dz)

    def sub(self, other: Vec3) -> Vec3:
        """Subtract another Vec3 from this vector."""
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def mul(self, factor: float) -> Vec3:
        """Multiply vector components by scalar factor."""
        return Vec3(self.x * factor, self.y * factor, self.z * factor)

    def to_block_pos(self) -> BlockPos:
        """Convert continuous coordinate to block integer coordinates via floor."""
        return BlockPos(math.floor(self.x), math.floor(self.y), math.floor(self.z))

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to (x, y, z) tuple."""
        return self.x, self.y, self.z
