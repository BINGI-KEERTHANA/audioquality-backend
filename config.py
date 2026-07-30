"""Runtime configuration sourced from environment variables."""

import logging
import os
from dataclasses import dataclass

DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5177",
    "http://127.0.0.1:5177",
)


def _positive_int_from_env(name: str, default: int) -> int:
    """Read a positive integer environment setting, falling back safely."""
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _origins_from_env() -> tuple[str, ...]:
    """Read a comma-separated allow-list for browser clients."""
    value = os.getenv("CORS_ORIGINS")
    if not value:
        return DEFAULT_CORS_ORIGINS
    origins = tuple(origin.strip() for origin in value.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


@dataclass(frozen=True)
class Settings:
    """Application settings that do not require extra configuration packages."""

    max_upload_bytes: int
    log_level: str
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS


def get_settings() -> Settings:
    """Build the immutable settings object from the process environment."""
    return Settings(
        max_upload_bytes=_positive_int_from_env(
            "MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        cors_origins=_origins_from_env(),
    )


def configure_logging(log_level: str) -> None:
    """Configure concise process logging when no host configuration exists."""
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
