"""Async tick scheduler: runs registered handlers at a fixed tick rate.

Perception, Decision, and Action layers register tick handlers here. Every
handler must be an ``async def`` and must never block the event loop; a handler
that takes longer than one tick window is reported via a warning log.
"""

import asyncio
import contextlib
import time
from collections.abc import Awaitable, Callable

import structlog

logger = structlog.get_logger(__name__)

TickHandler = Callable[[], Awaitable[None]]


class TickScheduler:
    """Calls registered handlers every ``1 / tick_rate`` seconds."""

    def __init__(self, tick_rate: int) -> None:
        if tick_rate < 1:
            raise ValueError(f"tick_rate must be >= 1, got {tick_rate}")
        self._tick_rate = tick_rate
        self._interval = 1.0 / tick_rate
        self._handlers: list[TickHandler] = []
        self._task: asyncio.Task[None] | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        """Whether the tick loop is currently active."""
        return self._running

    def register(self, handler: TickHandler) -> None:
        """Add a handler to be called once per tick."""
        self._handlers.append(handler)

    def unregister(self, handler: TickHandler) -> None:
        """Remove a previously registered handler."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    async def start(self) -> None:
        """Begin the background tick loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._tick_loop())

    async def stop(self) -> None:
        """Cancel the tick loop and wait for it to finish."""
        if not self._running:
            return
        self._running = False
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _tick_loop(self) -> None:
        logger.info("scheduler_started", tick_rate=self._tick_rate, interval=self._interval)
        try:
            while self._running:
                await self._run_tick()
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            logger.info("scheduler_stopped_gracefully")
            raise

    async def _run_tick(self) -> None:
        for handler in list(self._handlers):
            name = getattr(handler, "__name__", repr(handler))
            started = time.perf_counter()
            try:
                await handler()
            except Exception:
                logger.exception("tick_handler_error", handler=name)
            elapsed = time.perf_counter() - started
            if elapsed > self._interval:
                logger.warning("tick_handler_slow", handler=name, elapsed=elapsed)
