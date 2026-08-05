"""Pydantic-validated configuration models for ``config/config.yaml``.

Models are frozen after load so a validated config cannot be mutated at
runtime. Parsing and schema validation happen in :func:`load_config`, which
fails fast on bad YAML or a bad schema.
"""

from pydantic import BaseModel, ConfigDict, Field


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
