"""Tests for the tick scheduler."""

import asyncio

from miningcraft.core.scheduler import TickScheduler


async def test_start_and_stop() -> None:
    scheduler = TickScheduler(50)
    await scheduler.start()
    assert scheduler.is_running
    await scheduler.stop()
    assert not scheduler.is_running


async def test_handler_called_on_tick() -> None:
    scheduler = TickScheduler(50)
    calls: list[int] = []

    async def handler() -> None:
        calls.append(1)

    scheduler.register(handler)
    await scheduler.start()
    await asyncio.sleep(0.15)
    await scheduler.stop()
    assert len(calls) >= 2


async def test_multiple_handlers_all_called() -> None:
    scheduler = TickScheduler(50)
    first: list[int] = []
    second: list[int] = []

    async def handler_a() -> None:
        first.append(1)

    async def handler_b() -> None:
        second.append(1)

    scheduler.register(handler_a)
    scheduler.register(handler_b)
    await scheduler.start()
    await asyncio.sleep(0.15)
    await scheduler.stop()
    assert first
    assert second


async def test_unregister_removes_handler() -> None:
    scheduler = TickScheduler(50)
    calls: list[int] = []

    async def handler() -> None:
        calls.append(1)

    scheduler.register(handler)
    scheduler.unregister(handler)
    await scheduler.start()
    await asyncio.sleep(0.1)
    await scheduler.stop()
    assert calls == []


async def test_slow_handler_logs_warning(mocker) -> None:
    mock_logger = mocker.patch("miningcraft.core.scheduler.logger")
    scheduler = TickScheduler(50)

    async def slow_handler() -> None:
        await asyncio.sleep(0.05)

    scheduler.register(slow_handler)
    await scheduler.start()
    await asyncio.sleep(0.1)
    await scheduler.stop()
    assert mock_logger.warning.call_args_list


async def test_handler_exception_does_not_stop_loop(mocker) -> None:
    mocker.patch("miningcraft.core.scheduler.logger")
    scheduler = TickScheduler(50)
    calls: list[int] = []

    async def bad_handler() -> None:
        raise RuntimeError("boom")

    async def good_handler() -> None:
        calls.append(1)

    scheduler.register(bad_handler)
    scheduler.register(good_handler)
    await scheduler.start()
    await asyncio.sleep(0.15)
    await scheduler.stop()
    assert len(calls) >= 2


async def test_is_running_flag() -> None:
    scheduler = TickScheduler(50)
    assert not scheduler.is_running
    await scheduler.start()
    assert scheduler.is_running
    await scheduler.stop()
    assert not scheduler.is_running
