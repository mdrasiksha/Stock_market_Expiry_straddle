"""Market data models and demo snapshot factory for the 0DTE engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time


@dataclass(frozen=True)
class OptionQuote:
    """Normalized option quote used by strategy, Greeks, and liquidity engines."""

    strike: int
    option_type: str
    ltp: float
    bid: float
    ask: float
    iv: float
    oi: int
    volume: int
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0


@dataclass(frozen=True)
class MarketSnapshot:
    """Point-in-time market state required before taking a 0DTE trade."""

    underlying: str
    spot: float
    previous_close: float
    open_price: float
    high: float
    low: float
    vwap: float
    vwap_slope: float
    india_vix: float
    india_vix_change_pct: float
    adx: float
    atr: float
    supertrend_bullish: bool
    ema20: float
    ema50: float
    market_breadth: float
    pcr: float
    iv_rank: float
    iv_percentile: float
    option_iv: float
    option_iv_change_pct: float
    circuit_day: bool = False
    exchange_issue: bool = False
    rbi_policy: bool = False
    budget_day: bool = False
    major_global_event: bool = False
    weekly_monthly_overlap: bool = False
    no_existing_position: bool = True
    premium_decay_started: bool = True
    option_chain: list[OptionQuote] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def gap_pct(self) -> float:
        """Return opening gap percentage versus previous close."""
        return ((self.open_price - self.previous_close) / self.previous_close) * 100 if self.previous_close else 0.0

    @property
    def opening_range_pct(self) -> float:
        """Return high-low range as percentage of spot."""
        return ((self.high - self.low) / self.spot) * 100 if self.spot else 0.0

    @property
    def vwap_distance_pct(self) -> float:
        """Return absolute spot distance from VWAP as a percentage."""
        return abs(self.spot - self.vwap) / self.vwap * 100 if self.vwap else 0.0

    @property
    def opening_range_complete(self) -> bool:
        """Return True after the first 15 minutes of trading."""
        return self.timestamp.time() >= time(9, 30)


def demo_snapshot() -> MarketSnapshot:
    """Return deterministic paper-trading data when live feeds are unavailable."""
    spot = 24520.0
    chain = [
        OptionQuote(24400, "CE", 178, 177, 179, 13.8, 140000, 21000, 0.58, 0.0018, -22, 11),
        OptionQuote(24400, "PE", 82, 81, 83, 14.1, 132000, 19000, -0.42, 0.0017, -19, 10),
        OptionQuote(24500, "CE", 121, 120, 122, 13.5, 185000, 26000, 0.51, 0.0021, -25, 12),
        OptionQuote(24500, "PE", 115, 114, 116, 13.7, 192000, 27500, -0.49, 0.0020, -24, 12),
        OptionQuote(24600, "CE", 77, 76, 78, 13.9, 125000, 17000, 0.41, 0.0018, -18, 10),
        OptionQuote(24600, "PE", 169, 168, 171, 14.0, 118000, 16500, -0.59, 0.0019, -21, 11),
    ]
    return MarketSnapshot("NIFTY", spot, 24480, 24530, 24610, 24445, 24505, 0.01, 13.2, -1.4, 18.5, 96, True, 24510, 24485, 0.54, 0.98, 42, 49, 13.8, -0.7, option_chain=chain)
