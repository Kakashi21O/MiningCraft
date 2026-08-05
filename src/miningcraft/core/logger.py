"""Structured logging wrapper built on structlog.

Call :func:`configure_logging` once at startup (from ``engine.start``), then
obtain per-module loggers with ``get_logger(__name__)``. ``print()`` is never
used in production code — all output flows through these loggers.
"""

import structlog
from structlog.typing import FilteringBoundLogger, Processor

_PROCESSORS: list[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.TimeStamper(fmt="iso"),
]


def configure_logging(level: str, fmt: str) -> None:
    """Configure structlog once at startup.

    ``fmt`` selects JSON output for production or a colour pretty renderer for
    development. ``level`` is one of ``DEBUG``, ``INFO``, ``WARNING``,
    ``ERROR`` and filters log calls below that threshold.
    """
    if fmt == "json":
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()
    structlog.configure(
        processors=[*_PROCESSORS, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level.upper()),
    )


def get_logger(name: str) -> FilteringBoundLogger:
    """Return a bound logger for a module, typically ``__name__``."""
    return structlog.get_logger(name)
