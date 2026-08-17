"""Movement controller executing player rotation, stepping, and locomotion."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from minecraft.networking.packets.serverbound.play import PositionAndLookPacket

from miningcraft.core.logger import get_logger
from miningcraft.models.action import ActionResult
from miningcraft.models.position import Vec3

if TYPE_CHECKING:
    from miningcraft.action.safety import SafetyChecker
    from miningcraft.perception.player import PlayerStateCache
    from miningcraft.protocol.packets import PacketSender

logger = get_logger("action.movement")


def calculate_look_angles(
    current_pos: Vec3,
    target_pos: Vec3,
    eye_height: float = 1.62,
) -> tuple[float, float]:
    """Calculate the Minecraft yaw and pitch required to face target_pos from current_pos."""
    dx = target_pos.x - current_pos.x
    dy = target_pos.y - (current_pos.y + eye_height)
    dz = target_pos.z - current_pos.z

    # Minecraft yaw: 0 = South (+Z), 90 = West (-X), 180 = North (-Z), 270 = East (+X)
    yaw = math.degrees(math.atan2(-dx, dz))
    if yaw < 0:
        yaw += 360.0

    # Minecraft pitch: -90 = straight up, 90 = straight down
    dist_xz = math.hypot(dx, dz)
    pitch = math.degrees(-math.atan2(dy, dist_xz))
    pitch = max(-90.0, min(90.0, pitch))

    return round(yaw, 2), round(pitch, 2)


class MovementController:
    """Controls physical movement, rotation, jumping, and locomotion packets."""

    def __init__(
        self,
        packet_sender: PacketSender | None = None,
        player_cache: PlayerStateCache | None = None,
        safety_checker: SafetyChecker | None = None,
        step_size: float = 0.5,
        eye_height: float = 1.62,
    ) -> None:
        self._sender = packet_sender
        self._player = player_cache
        self._safety = safety_checker
        self.step_size = step_size
        self.eye_height = eye_height
        self._is_sprinting = False
        self._is_sneaking = False

    @property
    def current_position(self) -> Vec3:
        """Get the current estimated or cached player position."""
        if self._player is not None:
            return self._player.state.position
        return Vec3(0.0, 0.0, 0.0)

    @property
    def current_yaw(self) -> float:
        """Get the current cached yaw."""
        if self._player is not None:
            return self._player.state.yaw
        return 0.0

    @property
    def current_pitch(self) -> float:
        """Get the current cached pitch."""
        if self._player is not None:
            return self._player.state.pitch
        return 0.0

    @property
    def is_on_ground(self) -> bool:
        """Get the current cached on_ground state."""
        if self._player is not None:
            return self._player.state.on_ground
        return True

    def set_sprinting(self, enabled: bool) -> None:
        """Toggle sprinting flag."""
        self._is_sprinting = enabled
        logger.debug("sprint_state_changed", sprinting=enabled)

    def set_sneaking(self, enabled: bool) -> None:
        """Toggle sneaking flag."""
        self._is_sneaking = enabled
        logger.debug("sneak_state_changed", sneaking=enabled)

    async def send_position_and_look(
        self,
        pos: Vec3,
        yaw: float,
        pitch: float,
        on_ground: bool = True,
    ) -> ActionResult:
        """Emit a serverbound PositionAndLookPacket and update local player state."""
        packet = PositionAndLookPacket()
        packet.x = pos.x
        packet.feet_y = pos.y
        packet.z = pos.z
        packet.yaw = yaw
        packet.pitch = pitch
        packet.on_ground = on_ground

        if self._sender is not None:
            sent = await self._sender.send(packet)
            if not sent:
                logger.error("failed_to_send_position_and_look", pos=str(pos))
                return ActionResult.failed("Failed to send PositionAndLook packet")

        # Update local player state cache
        if self._player is not None:
            self._player.update_position(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                yaw=yaw,
                pitch=pitch,
                on_ground=on_ground,
            )

        return ActionResult.success(
            "Position and look updated",
            data={"pos": pos, "yaw": yaw, "pitch": pitch},
        )

    async def look_angles(self, yaw: float, pitch: float) -> ActionResult:
        """Rotate the player's camera to specific yaw and pitch angles."""
        norm_yaw = yaw % 360.0
        norm_pitch = max(-90.0, min(90.0, pitch))
        logger.debug("rotating_to_angles", yaw=norm_yaw, pitch=norm_pitch)
        return await self.send_position_and_look(
            pos=self.current_position,
            yaw=norm_yaw,
            pitch=norm_pitch,
            on_ground=self.is_on_ground,
        )

    async def look_at(self, target: Vec3) -> ActionResult:
        """Aim the player's camera directly towards a 3D coordinate."""
        curr = self.current_position
        yaw, pitch = calculate_look_angles(curr, target, eye_height=self.eye_height)
        logger.debug("looking_at_target", target=str(target), yaw=yaw, pitch=pitch)
        return await self.look_angles(yaw, pitch)

    async def step_towards(
        self,
        target: Vec3,
        max_step: float | None = None,
    ) -> ActionResult:
        """Take a single physics step towards the target position."""
        curr = self.current_position
        dist = curr.distance(target)
        if dist <= 0.01:
            return ActionResult.success("Already at target", data={"pos": curr})

        step_dist = max_step or self.step_size
        actual_step = min(dist, step_dist)

        # Direction vector
        dir_vec = target.sub(curr).normalize().mul(actual_step)
        next_pos = curr.add(dir_vec)

        # Safety check next position
        if self._safety is not None:
            safety_res = self._safety.check_position_safety(next_pos)
            if not safety_res.is_success:
                logger.warning(
                    "step_blocked_by_safety",
                    pos=str(next_pos),
                    reason=safety_res.message,
                )
                return safety_res

        yaw, pitch = calculate_look_angles(curr, target, eye_height=self.eye_height)
        return await self.send_position_and_look(
            pos=next_pos,
            yaw=yaw,
            pitch=pitch,
            on_ground=self.is_on_ground,
        )

    async def walk_to(
        self,
        target: Vec3,
        tolerance: float = 0.3,
        max_steps: int = 100,
    ) -> ActionResult:
        """Iteratively walk step-by-step towards the target position until within tolerance."""
        logger.info("walking_to_target", current=str(self.current_position), target=str(target))

        for step_idx in range(max_steps):
            curr = self.current_position
            if curr.distance(target) <= tolerance:
                logger.info("reached_target", pos=str(curr), steps=step_idx)
                return ActionResult.success("Reached target", data={"pos": curr, "steps": step_idx})

            res = await self.step_towards(target)
            if not res.is_success:
                logger.warning("walk_interrupted", step=step_idx, reason=res.message)
                return res

        msg = (
            f"Exceeded max steps ({max_steps}) without reaching target "
            f"(current: {self.current_position})"
        )
        return ActionResult.failed(msg)

    async def jump(self) -> ActionResult:
        """Perform a standard vertical jump."""
        curr = self.current_position
        jump_pos = Vec3(curr.x, curr.y + 1.25, curr.z)

        if self._safety is not None:
            safety_res = self._safety.check_position_safety(jump_pos)
            if not safety_res.is_success:
                return safety_res

        logger.debug("performing_jump", from_y=curr.y, to_y=jump_pos.y)
        return await self.send_position_and_look(
            pos=jump_pos,
            yaw=self.current_yaw,
            pitch=self.current_pitch,
            on_ground=False,
        )
