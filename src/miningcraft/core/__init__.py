"""Core Engine: shared infrastructure for all layers.

Events are the only allowed communication path between layers; the event bus,
logger, config, scheduler, and state manager live here. No layer may import
from this package's siblings above it.
"""

from miningcraft.core.config import AppConfig, ConfigError, load_config
from miningcraft.core.engine import Engine
from miningcraft.core.events import EventBus
from miningcraft.core.logger import configure_logging, get_logger
from miningcraft.core.scheduler import TickScheduler
from miningcraft.core.state import BotState, StateError, StateManager

__all__ = [
    "AppConfig",
    "BotState",
    "ConfigError",
    "Engine",
    "EventBus",
    "StateError",
    "StateManager",
    "TickScheduler",
    "configure_logging",
    "get_logger",
    "load_config",
]
