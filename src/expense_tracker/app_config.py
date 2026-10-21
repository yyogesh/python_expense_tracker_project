from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from expense_tracker.config import (
    DEFAULT_DATA_DIR,
    DEFAULT_LOG_LEVEL,
    ENV_FILE,
    LOG_FILE,
    LOGS_DIR,
)

DATA_DIR_VAR = "EXPENSE_TRACKER_DATA_DIR"
LOG_LEVEL_VAR = "EXPENSE_TRACKER_LOG_LEVEL"

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


class ConfigError(ValueError):
    """Raised when a setting has a value the app cannot use."""


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    log_level: str  # one of LOG_LEVELS

    @property
    def log_file(self) -> Path:
        return self.data_dir / LOGS_DIR / LOG_FILE


def load_config(
    env_file: Path | None = Path(ENV_FILE),
    environ: Mapping[str, str] | None = None,
) -> AppConfig:
    values = read_env_file(env_file) if env_file is not None else {}
    values.update(os.environ if environ is None else environ)

    return AppConfig(
        data_dir=_parse_data_dir(values.get(DATA_DIR_VAR)),
        log_level=_parse_log_level(values.get(LOG_LEVEL_VAR)),
    )


def read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return {
        name: value
        for name, value in dotenv_values(path, encoding="utf-8").items()
        if value is not None
    }


def _parse_data_dir(text: str | None) -> Path:
    if text is None or not text.strip():
        text = DEFAULT_DATA_DIR
    return Path(text.strip()).expanduser()


def _parse_log_level(text: str | None) -> str:
    if text is None or not text.strip():
        return DEFAULT_LOG_LEVEL
    level = text.strip().upper()  # "debug" is fine too
    if level not in LOG_LEVELS:
        raise ConfigError(
            f"{LOG_LEVEL_VAR} must be one of {', '.join(LOG_LEVELS)}, not {text!r}."
        )
    return level
