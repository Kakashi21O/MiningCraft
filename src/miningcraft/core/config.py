"""Pydantic-validated configuration models for ``config/config.yaml``.

Models are frozen after load so a validated config cannot be mutated at
runtime. Parsing and schema validation happen in :func:`load_config`, which
fails fast on bad YAML or a bad schema.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ConfigError(Exception):
    """Raised when configuration cannot be loaded or validated."""


class ServerConfig(BaseModel):
    """Minecraft server connection settings."""

    model_config = ConfigDict(frozen=True)

    host: str
    port: int = Field(ge=1, le=65535)
    version: str


class BotConfig(BaseModel):
    """Bot identity settings."""

    model_config = ConfigDict(frozen=True)

    username: str


class EngineConfig(BaseModel):
    """Core Engine settings."""

    model_config = ConfigDict(frozen=True)

    tick_rate: int = Field(default=20, ge=1)


class MiningConfig(BaseModel):
    """Mining module settings."""

    model_config = ConfigDict(frozen=True)

    tunnel_length: int
    branch_spacing: int
    speed: float


class SafetyConfig(BaseModel):
    """Safety thresholds."""

    model_config = ConfigDict(frozen=True)

    lava_distance: int
    water_distance: int


class LoggingConfig(BaseModel):
    """Logging settings consumed by :func:`miningcraft.core.logger.configure_logging`."""

    model_config = ConfigDict(frozen=True)

    level: str
    format: str


class AppConfig(BaseModel):
    """Top-level configuration aggregate."""

    model_config = ConfigDict(frozen=True)

    server: ServerConfig
    bot: BotConfig
    engine: EngineConfig
    mining: MiningConfig
    safety: SafetyConfig
    logging: LoggingConfig


def load_config(path: Path) -> AppConfig:
    """Load and validate a YAML config file, failing fast on any problem.

    Raises :class:`ConfigError` for a missing file, invalid YAML, or a schema
    violation. Never silently falls back to defaults.
    """
    try:
        with path.open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise ConfigError(f"config file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc
    try:
        return AppConfig.model_validate(raw or {})
    except ValidationError as exc:
        raise ConfigError(f"invalid config schema in {path}: {exc}") from exc
