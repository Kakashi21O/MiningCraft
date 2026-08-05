"""Tests for the bot state machine."""

import pytest

from miningcraft.core.state import BotState, StateError, StateManager


def test_initial_state_is_idle() -> None:
    assert StateManager().current is BotState.IDLE


def test_valid_transition() -> None:
    manager = StateManager()
    manager.transition(BotState.CONNECTING)
    assert manager.current is BotState.CONNECTING
    manager.transition(BotState.CONNECTED)
    assert manager.current is BotState.CONNECTED


def test_invalid_transition_raises() -> None:
    manager = StateManager()
    with pytest.raises(StateError):
        manager.transition(BotState.MINING)


def test_reset_returns_to_idle() -> None:
    manager = StateManager()
    manager.transition(BotState.CONNECTING)
    manager.reset()
    assert manager.current is BotState.IDLE


def test_every_transition_is_logged(mocker: pytest.MockFixture) -> None:
    mock_logger = mocker.patch("miningcraft.core.state.logger")
    manager = StateManager()
    manager.transition(BotState.CONNECTING)
    mock_logger.info.assert_called_once()


def test_all_states_defined_in_enum() -> None:
    names = {state.name for state in BotState}
    assert names == {
        "IDLE",
        "CONNECTING",
        "CONNECTED",
        "MINING",
        "RETURNING",
        "TOOL_SWITCH",
        "STOPPING",
        "ERROR",
        "DISCONNECTED",
    }


def test_state_error_message_includes_states() -> None:
    manager = StateManager()
    with pytest.raises(StateError, match="idle.*mining"):
        manager.transition(BotState.MINING)
