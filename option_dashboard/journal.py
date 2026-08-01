"""CSV-backed trade journal for complete trade lifecycle records."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from config import settings
from storage import screenshot_placeholder

JOURNAL_COLUMNS = ["Date", "Underlying", "Expiry", "Strike", "Strategy", "Market Type", "Trade Score", "Entry Premium", "Exit Premium", "Entry Time", "Exit Time", "Holding Minutes", "Profit", "Profit %", "Reason", "Screenshot", "Mistakes", "Learning Notes", "30 Target", "50 Target", "60 Target", "70 Target", "Stop Loss", "Manual Exit"]


class TradeJournal:
    """Append-only journal writer for completed trades."""

    def __init__(self, path: Path = settings.journal_path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists() or self.path.stat().st_size == 0:
            self.path.write_text(",".join(JOURNAL_COLUMNS) + "\n", encoding="utf-8")

    def append_trade(self, row: dict[str, Any], capture_screenshot: bool = True) -> None:
        """Append a completed trade with strategy, score, regime, notes, and screenshot path."""
        payload = dict(row)
        if capture_screenshot and not payload.get("Screenshot"):
            payload["Screenshot"] = str(screenshot_placeholder(settings.screenshot_dir))
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=JOURNAL_COLUMNS)
            writer.writerow({column: payload.get(column, "") for column in JOURNAL_COLUMNS})
