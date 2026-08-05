"""Shared fixtures for protocol layer tests.

The real Event Bus is part of the Core Engine (v0.3.0). Until then, tests use
this minimal dict-backed stub that records every published event.
"""

from typing import Any

import pytest


class EventBusStub:
    """Minimal event bus that records publishes, satisfying the EventBus protocol."""

    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []

    def publish(self, event_name: str, **kwargs: Any) -> None:
        self.published.append((event_name, kwargs))

    @property
    def event_names(self) -> list[str]:
        return [name for name, _ in self.published]

    def assert_published(self, event_name: str) -> None:
        assert event_name in self.event_names, (
            f"expected event {event_name!r} to be published; got {self.event_names!r}"
        )


@pytest.fixture
def event_bus() -> EventBusStub:
    return EventBusStub()
