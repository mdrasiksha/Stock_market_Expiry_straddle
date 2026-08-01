"""Exit signal generation for live 0DTE positions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from market import MarketSnapshot


@dataclass(frozen=True)
class ExitSignal:
    """Exit-engine result."""

    should_exit: bool
    reasons: list[str]


def exit_signal(market: MarketSnapshot, combined: float, entry: float, target_pct: float, sl_pct: float) -> ExitSignal:
    """Evaluate combined SL, target, VWAP, ADX, IV, time, reversal, and premium expansion exits."""
    reasons: list[str] = []
    if combined >= entry * (1 + sl_pct / 100):
        reasons.append("Combined SL")
    if combined <= entry * (1 - target_pct / 100):
        reasons.append("Target")
    if market.vwap_distance_pct > 0.45:
        reasons.append("VWAP Break")
    if market.adx > 25:
        reasons.append("ADX Rising")
    if market.option_iv_change_pct > 5:
        reasons.append("IV Spike")
    if market.timestamp.time() > time(15, 20):
        reasons.append("Time >3:20")
    if (market.supertrend_bullish and market.ema20 < market.ema50) or (not market.supertrend_bullish and market.ema20 > market.ema50):
        reasons.append("Trend Reversal")
    if combined > entry * 1.1:
        reasons.append("Premium Expansion")
    return ExitSignal(bool(reasons), reasons)
