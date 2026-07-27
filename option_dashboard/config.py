"""Application configuration loaded from environment variables."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"

if not ENV_PATH.is_file():
    raise FileNotFoundError(f"Required .env file not found at: {ENV_PATH}")

print(f"Resolved .env path: {ENV_PATH}")
DOTENV_LOADED = load_dotenv(dotenv_path=ENV_PATH)
print(f"load_dotenv() succeeded: {DOTENV_LOADED}")
print(f"API_KEY loaded: {bool(os.getenv('API_KEY'))}")
print(f"API_SECRET loaded: {bool(os.getenv('API_SECRET'))}")
print(f"ACCESS_TOKEN loaded: {bool(os.getenv('ACCESS_TOKEN'))}")

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=LOG_FORMAT)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Option Dashboard."""

    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("API_SECRET", ""))
    access_token: str = field(default_factory=lambda: os.getenv("ACCESS_TOKEN", ""))
    refresh_interval: int = field(
        default_factory=lambda: int(os.getenv("REFRESH_INTERVAL", "2"))
    )
    journal_path: Path = field(default_factory=lambda: PROJECT_ROOT / "trades.csv")
    success_sound: Path = field(
        default_factory=lambda: PROJECT_ROOT / "assets" / "success.wav"
    )
    alarm_sound: Path = field(
        default_factory=lambda: PROJECT_ROOT / "assets" / "alarm.wav"
    )

    @property
    def is_configured(self) -> bool:
        """Return True when Kite credentials required for live monitoring exist."""
        return bool(self.api_key and self.access_token)


def validate_configuration() -> None:
    """Raise a descriptive exception when required credentials are missing."""
    missing_keys = [
        key
        for key in ("API_KEY", "API_SECRET", "ACCESS_TOKEN")
        if not os.getenv(key)
    ]

    if missing_keys:
        missing = ", ".join(missing_keys)
        raise RuntimeError(f"Missing required environment variable(s): {missing}")


settings = Settings()
