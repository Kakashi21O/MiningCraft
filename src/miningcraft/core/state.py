"""Bot state machine: single owner and single source of truth for bot state.

``StateManager`` tracks the bot's current state and enforces a fixed map of
valid transitions. Every transition is logged; an invalid one raises
:class:`StateError`.
"""

from enum import Enum

import structlog

logger = structlog.get_logger(__name__)


class BotState(Enum):
    """All states the bot can be in."""

    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    MINING = "mining"
    RETURNING = "returning"
    TOOL_SWITCH = "tool_switch"
    STOPPING = "stopping"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class StateError(Exception):
    """Raised when a state transition is not allowed."""


class StateManager:
    """Tracks the bot's current state and enforces valid transitions."""

    _TRANSITIONS: dict[BotState, set[BotState]] = {
        BotState.IDLE: {BotState.CONNECTING, BotState.DISCONNECTED},
        BotState.CONNECTING: {BotState.CONNECTED, BotState.DISCONNECTED, BotState.ERROR},
        BotState.CONNECTED: {BotState.MINING, BotState.DISCONNECTED, BotState.STOPPING},
        BotState.MINING: {
            BotState.RETURNING,
            BotState.STOPPING,
            BotState.TOOL_SWITCH,
            BotState.DISCONNECTED,
        },
        BotState.RETURNING: {BotState.MINING, BotState.DISCONNECTED},
        BotState.TOOL_SWITCH: {BotState.MINING},
        BotState.STOPPING: {BotState.IDLE, BotState.DISCONNECTED},
        BotState.ERROR: {BotState.IDLE, BotState.DISCONNECTED},
        BotState.DISCONNECTED: {BotState.CONNECTING, BotState.IDLE},
    }

    def __init__(self) -> None:
        self._current = BotState.IDLE

    @property
    def current(self) -> BotState:
        """The bot's current state."""
        return self._current

    def transition(self, new_state: BotState) -> None:
        """Move to ``new_state``, raising :class:`StateError` if not allowed."""
        old = self._current
        if new_state not in self._TRANSITIONS[old]:
            raise StateError(f"invalid transition: {old.value} -> {new_state.value}")
        self._current = new_state
        logger.info("state_transition", old_state=old.value, new_state=new_state.value)

    def reset(self) -> None:
        """Return to :attr:`BotState.IDLE`."""
        old = self._current
        self._current = BotState.IDLE
        if old is not BotState.IDLE:
            logger.info("state_transition", old_state=old.value, new_state=BotState.IDLE.value)
