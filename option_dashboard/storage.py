"""Persistence helpers for CSV artifacts and screenshots."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


def append_csv(path: Path, row: dict[str, object]) -> None:
    """Append a row to CSV, creating headers when the file does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame([row])
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)


def screenshot_placeholder(directory: Path, prefix: str = "trade") -> Path:
    """Create a lightweight screenshot placeholder for audit trails."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}.txt"
    path.write_text("Screenshot capture placeholder. Use browser/Streamlit exporter in production.\n", encoding="utf-8")
    return path
