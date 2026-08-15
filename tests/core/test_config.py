"""Tests for the Pydantic config loader."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from miningcraft.core.config import AppConfig, ConfigError, load_config

VALID_CONFIG: dict[str, object] = {
    "server": {"host": "localhost", "port": 25565, "version": "1.20.1"},
    "bot": {"username": "MiningBot"},
    "engine": {"tick_rate": 20},
    "mining": {"tunnel_length": 64, "branch_spacing": 3, "speed": 1.0},
    "safety": {"lava_distance": 3, "water_distance": 2},
    "logging": {"level": "INFO", "format": "json"},
}


def _write_config(tmp_path: Path, data: dict[str, object]) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_load_valid_config(tmp_path: Path) -> None:
    config = load_config(_write_config(tmp_path, VALID_CONFIG))
    assert config.server.host == "localhost"
    assert config.server.port == 25565
    assert config.bot.username == "MiningBot"
    assert config.engine.tick_rate == 20
    assert config.logging.level == "INFO"


def test_load_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.yaml")


def test_load_invalid_yaml_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("server: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(path)


def test_load_missing_required_field_raises(tmp_path: Path) -> None:
    data = dict(VALID_CONFIG)
    del data["server"]
    with pytest.raises(ConfigError):
        load_config(_write_config(tmp_path, data))


def test_load_invalid_port_raises(tmp_path: Path) -> None:
    data = dict(VALID_CONFIG)
    data["server"] = {**data["server"], "port": 70000}
    with pytest.raises(ConfigError):
        load_config(_write_config(tmp_path, data))


def test_config_is_frozen(tmp_path: Path) -> None:
    config = load_config(_write_config(tmp_path, VALID_CONFIG))
    with pytest.raises(ValidationError):
        config.server.host = "other"


def test_config_defaults_applied(tmp_path: Path) -> None:
    data = dict(VALID_CONFIG)
    data["engine"] = {}
    config = load_config(_write_config(tmp_path, data))
    assert config.engine.tick_rate == 20


def test_inject_custom_path(tmp_path: Path) -> None:
    path = _write_config(tmp_path, VALID_CONFIG)
    config = load_config(path)
    assert isinstance(config, AppConfig)
    assert config.bot.username == "MiningBot"
