"""Engine lifecycle: initialises, runs, and shuts down the Core Engine.

The engine wires Logger → Config → EventBus → StateManager → Scheduler. It does
not connect to Minecraft yet — that wiring arrives with the Mining Engine
(v1.0.0).
"""

import asyncio

from miningcraft.core.config import AppConfig
from miningcraft.core.events import EventBus
from miningcraft.core.logger import configure_logging, get_logger
from miningcraft.core.scheduler import TickScheduler
from miningcraft.core.state import StateManager

logger = get_logger(__name__)


class Engine:
    """Single entry point for the bot: ``start`` → ``run`` → ``stop``."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._event_bus = EventBus()
        self._state = StateManager()
        self._scheduler = TickScheduler(config.engine.tick_rate)
        self._running = False

    @property
    def config(self) -> AppConfig:
        """The validated application configuration."""
        return self._config

    @property
    def event_bus(self) -> EventBus:
        """The shared event bus."""
        return self._event_bus

    @property
    def state(self) -> StateManager:
        """The shared state manager."""
        return self._state

    @property
    def scheduler(self) -> TickScheduler:
        """The shared tick scheduler."""
        return self._scheduler

    async def start(self) -> None:
        """Configure logging, wire components, and start the tick loop."""
        configure_logging(self._config.logging.level, self._config.logging.format)
        logger.info("engine_start", tick_rate=self._config.engine.tick_rate)
        await self._scheduler.start()
        self._running = True

    async def run(self) -> None:
        """Keep the process alive until :meth:`stop` is called."""
        while self._running:
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        """Gracefully stop the scheduler and return the bot to IDLE."""
        if not self._running and not self._scheduler.is_running:
            return
        self._running = False
        await self._scheduler.stop()
        self._state.reset()
        logger.info("engine_stop")
