"""Application configuration and trading-system defaults."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format=LOG_FORMAT)


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the AI-powered 0DTE trading system."""

    api_key: str = field(default_factory=lambda: os.getenv("API_KEY", ""))
    api_secret: str = field(default_factory=lambda: os.getenv("API_SECRET", ""))
    access_token: str = field(default_factory=lambda: os.getenv("ACCESS_TOKEN", ""))
    refresh_interval: int = field(default_factory=lambda: int(os.getenv("REFRESH_INTERVAL", "2")))
    capital: float = field(default_factory=lambda: float(os.getenv("CAPITAL", "500000")))
    risk_percent: float = field(default_factory=lambda: float(os.getenv("RISK_PERCENT", "1.0")))
    sl_percent: float = field(default_factory=lambda: float(os.getenv("SL_PERCENT", "30")))
    target_percent: float = field(default_factory=lambda: float(os.getenv("TARGET_PERCENT", "50")))
    vix_threshold: float = field(default_factory=lambda: float(os.getenv("VIX_THRESHOLD", "18")))
    paper_trading: bool = field(default_factory=lambda: os.getenv("PAPER_TRADING", "true").lower() == "true")
    broker: str = field(default_factory=lambda: os.getenv("BROKER", "Dummy"))
    theme: str = field(default_factory=lambda: os.getenv("THEME", "Dark"))
    auto_exit: bool = field(default_factory=lambda: os.getenv("AUTO_EXIT", "false").lower() == "true")
    auto_refresh: bool = field(default_factory=lambda: os.getenv("AUTO_REFRESH", "true").lower() == "true")
    journal_path: Path = field(default_factory=lambda: PROJECT_ROOT / "trades.csv")
    screenshot_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "screenshots")
    success_sound: Path = field(default_factory=lambda: PROJECT_ROOT / "assets" / "success.wav")
    alarm_sound: Path = field(default_factory=lambda: PROJECT_ROOT / "assets" / "alarm.wav")

    @property
    def is_configured(self) -> bool:
        """Return True when Kite credentials required for live monitoring exist."""
        return bool(self.api_key and self.access_token)


settings = Settings()
