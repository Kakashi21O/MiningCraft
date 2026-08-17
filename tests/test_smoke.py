"""Smoke tests for the repository skeleton."""

import miningcraft


def test_package_exports_version() -> None:
    """The top-level package exposes the current version."""
    assert miningcraft.__version__ == "0.5.0"
