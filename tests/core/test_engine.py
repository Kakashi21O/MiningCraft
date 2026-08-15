"""Tests for the engine lifecycle."""

from miningcraft.core.config import AppConfig
from miningcraft.core.engine import Engine
from miningcraft.core.events import EventBus
from miningcraft.core.scheduler import TickScheduler
from miningcraft.core.state import BotState, StateManager


async def test_engine_starts_and_stops(app_config: AppConfig) -> None:
    engine = Engine(app_config)
    await engine.start()
    assert engine.state.current is BotState.IDLE
    await engine.stop()
    assert engine.state.current is BotState.IDLE


async def test_engine_exposes_event_bus(app_config: AppConfig) -> None:
    assert isinstance(Engine(app_config).event_bus, EventBus)


async def test_engine_exposes_state_manager(app_config: AppConfig) -> None:
    assert isinstance(Engine(app_config).state, StateManager)


async def test_engine_exposes_scheduler(app_config: AppConfig) -> None:
    assert isinstance(Engine(app_config).scheduler, TickScheduler)


async def test_engine_stop_is_idempotent(app_config: AppConfig) -> None:
    engine = Engine(app_config)
    await engine.start()
    await engine.stop()
    await engine.stop()
