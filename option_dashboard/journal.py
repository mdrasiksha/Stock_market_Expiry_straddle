"""CSV-backed trade journal."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from config import settings

JOURNAL_COLUMNS = ["Date", "Underlying", "Expiry", "Strike", "Entry Premium", "Exit Premium", "Entry Time", "Exit Time", "Holding Minutes", "Profit", "Profit %", "Reason", "30 Target", "50 Target", "60 Target", "70 Target", "Stop Loss", "Manual Exit"]


class TradeJournal:
    """Append-only journal writer for completed trades."""

    def __init__(self, path: Path = settings.journal_path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(",".join(JOURNAL_COLUMNS) + "\n", encoding="utf-8")

    def append_trade(self, row: dict[str, Any]) -> None:
        """Append a completed trade without overwriting previous records."""
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=JOURNAL_COLUMNS)
            writer.writerow({column: row.get(column, "") for column in JOURNAL_COLUMNS})
