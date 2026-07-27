"""Application configuration loaded from environment variables."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=LOG_FORMAT)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the Option Dashboard."""

    api_key: str = os.getenv("API_KEY", "")
    api_secret: str = os.getenv("API_SECRET", "")
    access_token: str = os.getenv("ACCESS_TOKEN", "")
    refresh_interval: int = int(os.getenv("REFRESH_INTERVAL", "2"))
    journal_path: Path = BASE_DIR / "trades.csv"
    success_sound: Path = BASE_DIR / "assets" / "success.wav"
    alarm_sound: Path = BASE_DIR / "assets" / "alarm.wav"

    @property
    def is_configured(self) -> bool:
        """Return True when Kite credentials required for live monitoring exist."""
        return bool(self.api_key and self.access_token)


settings = Settings()
