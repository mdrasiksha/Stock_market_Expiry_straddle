"""Pure calculation helpers for option premium monitoring."""
from __future__ import annotations

from datetime import datetime, timezone


def combined_premium(ce_price: float, pe_price: float) -> float:
    """Return combined CE and PE option premium."""
    return round(float(ce_price) + float(pe_price), 2)


def mtm(entry_premium: float, current_premium: float, quantity: int) -> float:
    """Return mark-to-market P&L for a short straddle."""
    return round((float(entry_premium) - float(current_premium)) * abs(int(quantity)), 2)


def profit_percent(entry_premium: float, current_premium: float) -> float:
    """Return profit percentage against entry premium."""
    if entry_premium <= 0:
        return 0.0
    return round(((entry_premium - current_premium) / entry_premium) * 100, 2)


def premium_decay(entry_premium: float, current_premium: float) -> float:
    """Return premium decay percentage."""
    return max(0.0, profit_percent(entry_premium, current_premium))


def roi(profit: float, margin: float | None = None, fallback_capital: float | None = None) -> float:
    """Return ROI percentage using margin when supplied, otherwise fallback capital."""
    capital = margin or fallback_capital or 0.0
    if capital <= 0:
        return 0.0
    return round((profit / capital) * 100, 2)


def target_premium(entry_premium: float, target_percent: float) -> float:
    """Return premium level at which a short premium target is reached."""
    return round(entry_premium * (1 - target_percent / 100), 2)


def stop_loss_premium(entry_premium: float, sl_percent: float) -> float:
    """Return combined premium level at which stop loss is hit."""
    return round(entry_premium * (1 + sl_percent / 100), 2)


def target_status(entry_premium: float, current_premium: float, target_percent: float) -> str:
    """Return Reached when current premium is at or below the target premium."""
    return "Reached" if current_premium <= target_premium(entry_premium, target_percent) else "Pending"


def sl_distance(current_premium: float, sl_level: float) -> float:
    """Return distance remaining before stop-loss premium is reached."""
    return round(sl_level - current_premium, 2)


def holding_minutes(entry_time: datetime, now: datetime | None = None) -> float:
    """Return holding time in minutes."""
    current = now or datetime.now(timezone.utc)
    if entry_time.tzinfo is None:
        entry_time = entry_time.replace(tzinfo=timezone.utc)
    return round(max(0.0, (current - entry_time).total_seconds() / 60), 2)


def holding_time_label(entry_time: datetime, now: datetime | None = None) -> str:
    """Return human-readable holding time."""
    minutes = int(holding_minutes(entry_time, now))
    hours, mins = divmod(minutes, 60)
    return f"{hours:02d}:{mins:02d}"
