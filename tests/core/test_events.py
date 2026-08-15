"""Tests for the Core Engine event bus."""

from threading import Thread

from miningcraft.core.events import EventBus


def test_subscribe_and_publish() -> None:
    bus = EventBus()
    received: list[dict[str, int]] = []
    bus.subscribe("OnX", lambda **kw: received.append(kw))
    bus.publish("OnX", value=1)
    assert received == [{"value": 1}]


def test_multiple_handlers_called_in_order() -> None:
    bus = EventBus()
    order: list[int] = []
    bus.subscribe("OnX", lambda **kw: order.append(1))
    bus.subscribe("OnX", lambda **kw: order.append(2))
    bus.publish("OnX")
    assert order == [1, 2]


def test_unsubscribe_removes_handler() -> None:
    bus = EventBus()
    calls: list[int] = []

    def handler(**kw: object) -> None:
        calls.append(1)

    bus.subscribe("OnX", handler)
    bus.unsubscribe("OnX", handler)
    bus.publish("OnX")
    assert calls == []


def test_publish_unknown_event_does_nothing() -> None:
    bus = EventBus()
    bus.publish("OnUnknown", value=1)


def test_handler_error_does_not_stop_other_handlers(mocker) -> None:
    mocker.patch("miningcraft.core.events.logger")
    bus = EventBus()
    calls: list[int] = []

    def bad_handler(**kw: object) -> None:
        raise ValueError("boom")

    def good_handler(**kw: object) -> None:
        calls.append(1)

    bus.subscribe("OnX", bad_handler)
    bus.subscribe("OnX", good_handler)
    bus.publish("OnX")
    assert calls == [1]


async def test_publish_async_awaits_handler() -> None:
    bus = EventBus()
    awaited: list[int] = []

    async def handler(**kw: object) -> None:
        awaited.append(1)

    bus.subscribe("OnX", handler)
    await bus.publish_async("OnX")
    assert awaited == [1]


def test_clear_removes_all_handlers() -> None:
    bus = EventBus()
    calls: list[int] = []

    def handler(**kw: object) -> None:
        calls.append(1)

    bus.subscribe("OnX", handler)
    bus.clear()
    bus.publish("OnX")
    assert calls == []


def test_clear_specific_event() -> None:
    bus = EventBus()
    x_calls: list[int] = []
    y_calls: list[int] = []
    bus.subscribe("OnX", lambda **kw: x_calls.append(1))
    bus.subscribe("OnY", lambda **kw: y_calls.append(1))
    bus.clear("OnX")
    bus.publish("OnX")
    bus.publish("OnY")
    assert x_calls == []
    assert y_calls == [1]


def test_duplicate_subscribe_idempotent() -> None:
    bus = EventBus()
    calls: list[int] = []

    def handler(**kw: object) -> None:
        calls.append(1)

    bus.subscribe("OnX", handler)
    bus.subscribe("OnX", handler)
    bus.publish("OnX")
    assert calls == [1]


def test_thread_safe_subscribe() -> None:
    bus = EventBus()
    calls: list[int] = []

    def worker() -> None:
        for _ in range(100):
            bus.subscribe("OnX", lambda **kw: calls.append(1))

    threads = [Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    bus.publish("OnX")
    assert len(calls) == 400
