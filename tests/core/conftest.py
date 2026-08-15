"""Shared fixtures for Core Engine tests."""

import pytest

from miningcraft.core.config import AppConfig

VALID_CONFIG: dict[str, object] = {
    "server": {"host": "localhost", "port": 25565, "version": "1.20.1"},
    "bot": {"username": "MiningBot"},
    "engine": {"tick_rate": 20},
    "mining": {"tunnel_length": 64, "branch_spacing": 3, "speed": 1.0},
    "safety": {"lava_distance": 3, "water_distance": 2},
    "logging": {"level": "INFO", "format": "json"},
}


@pytest.fixture
def app_config() -> AppConfig:
    """A valid, fully-populated application config."""
    return AppConfig.model_validate(VALID_CONFIG)
