"""Mining and interaction controller for block breaking, placement, and arm swings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from minecraft.networking.packets.serverbound.play import (
    AnimationPacket,
    PlayerBlockPlacementPacket,
)

from miningcraft.core.logger import get_logger
from miningcraft.models.action import ActionResult, BlockFace, Hand
from miningcraft.models.position import BlockPos

if TYPE_CHECKING:
    from miningcraft.action.movement import MovementController
    from miningcraft.perception.world import WorldCache
    from miningcraft.protocol.packets import PacketSender

logger = get_logger("action.mining")


class MiningController:
    """Controls block breaking, placing, and physical arm interactions."""

    def __init__(
        self,
        packet_sender: PacketSender | None = None,
        world_cache: WorldCache | None = None,
        movement: MovementController | None = None,
    ) -> None:
        self._sender = packet_sender
        self._world = world_cache
        self._movement = movement
        self._current_dig_pos: BlockPos | None = None
        self._digging = False

    @property
    def is_digging(self) -> bool:
        """Return whether a block digging sequence is currently in progress."""
        return self._digging

    @property
    def current_target(self) -> BlockPos | None:
        """Get the block position currently being mined."""
        return self._current_dig_pos

    async def swing_arm(self, hand: Hand = Hand.MAIN_HAND) -> ActionResult:
        """Emit an arm swing animation packet."""
        packet = AnimationPacket()
        packet.hand = (
            AnimationPacket.HAND_MAIN if hand == Hand.MAIN_HAND else AnimationPacket.HAND_OFF
        )
        if self._sender is not None:
            sent = await self._sender.send(packet)
            if not sent:
                logger.error("failed_to_send_swing_arm_packet")
                return ActionResult.failed("Failed to send arm animation packet")
        logger.debug("arm_swung", hand=hand.name)
        return ActionResult.success("Arm swung", data={"hand": hand})

    async def start_digging(
        self,
        pos: BlockPos,
        face: BlockFace = BlockFace.TOP,
    ) -> ActionResult:
        """Begin breaking a block at the specified position."""
        logger.info("start_digging", pos=str(pos), face=face.name)

        # Look towards the block center if movement controller is available
        if self._movement is not None:
            await self._movement.look_at(pos.to_vec3())

        # Swing arm
        await self.swing_arm(Hand.MAIN_HAND)

        self._current_dig_pos = pos
        self._digging = True

        return ActionResult.success(
            "Started digging block",
            data={"pos": pos, "face": face},
        )

    async def cancel_digging(
        self,
        pos: BlockPos | None = None,
        face: BlockFace = BlockFace.TOP,
    ) -> ActionResult:
        """Cancel an ongoing block break sequence."""
        target_pos = pos or self._current_dig_pos
        if target_pos is None:
            return ActionResult.success("No active block digging to cancel")

        logger.info("cancel_digging", pos=str(target_pos), face=face.name)
        self._current_dig_pos = None
        self._digging = False
        return ActionResult.success("Cancelled digging", data={"pos": target_pos})

    async def finish_digging(
        self,
        pos: BlockPos,
        face: BlockFace = BlockFace.TOP,
    ) -> ActionResult:
        """Complete block destruction and update local world cache to air."""
        logger.info("finish_digging", pos=str(pos), face=face.name)
        await self.swing_arm(Hand.MAIN_HAND)

        # Update world cache block state to air (id 0)
        if self._world is not None:
            self._world.set_block(pos, state_id=0, name="minecraft:air")

        self._current_dig_pos = None
        self._digging = False
        return ActionResult.success("Finished digging block", data={"pos": pos})

    async def dig_block(
        self,
        pos: BlockPos,
        face: BlockFace = BlockFace.TOP,
    ) -> ActionResult:
        """Execute a full discrete dig sequence on a single block."""
        start_res = await self.start_digging(pos, face)
        if not start_res.is_success:
            return start_res

        return await self.finish_digging(pos, face)

    async def place_block(
        self,
        pos: BlockPos,
        face: BlockFace = BlockFace.TOP,
        hand: Hand = Hand.MAIN_HAND,
    ) -> ActionResult:
        """Place a block against a target block face."""
        logger.info("place_block", target_pos=str(pos), face=face.name, hand=hand.name)

        if self._movement is not None:
            await self._movement.look_at(pos.to_vec3())

        await self.swing_arm(hand)

        packet = PlayerBlockPlacementPacket()
        if self._sender is not None:
            sent = await self._sender.send(packet)
            if not sent:
                return ActionResult.failed("Failed to send block placement packet")

        placed_pos = pos.offset(face.offset.x, face.offset.y, face.offset.z)
        return ActionResult.success(
            "Placed block",
            data={"target_pos": pos, "placed_pos": placed_pos, "face": face},
        )
