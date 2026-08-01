"""Market-regime classifier and automatic strategy/strike selection."""
from __future__ import annotations

from dataclasses import dataclass

from market import MarketSnapshot, OptionQuote


@dataclass(frozen=True)
class RegimeResult:
    """Detected intraday regime with confidence."""

    regime: str
    confidence: float
    reasons: list[str]


@dataclass(frozen=True)
class StrikeSelection:
    """Recommended strikes and expected option-selling statistics."""

    atm: int
    otm1: int
    otm2: int
    recommended_call: int
    recommended_put: int
    expected_premium: float
    expected_theta: float
    expected_pop: float


@dataclass(frozen=True)
class StrategyRecommendation:
    """Strategy output generated from regime and strikes."""

    name: str
    strike_selection: StrikeSelection
    confidence: float
    rationale: str


class MarketRegimeDetector:
    """Classify market state using VWAP, ATR, ADX, trend, breadth, and opening range."""

    def detect(self, market: MarketSnapshot) -> RegimeResult:
        reasons: list[str] = []
        if market.adx > 30 or market.opening_range_pct > 0.8:
            return RegimeResult("NO TRADE", 88, ["Strong trend/range expansion risk"])
        if market.india_vix > 18 or market.iv_rank > 75:
            return RegimeResult("VOLATILE", 82, ["High VIX or elevated IV rank"])
        if market.adx > 25 and abs(market.ema20 - market.ema50) / market.spot > 0.002:
            return RegimeResult("TRENDING", 78, ["ADX above trend threshold", "EMA20/EMA50 separation"])
        if market.opening_range_pct > 0.6 or market.atr / market.spot > 0.006:
            return RegimeResult("EXPANSION", 76, ["Opening range or ATR expanding"])
        if market.vwap_distance_pct <= 0.25 and abs(market.vwap_slope) <= 0.03 and 0.8 <= market.pcr <= 1.2:
            reasons.extend(["Price near flat VWAP", "Neutral PCR", "Controlled opening range"])
            return RegimeResult("SIDEWAYS", 89, reasons)
        return RegimeResult("MEAN REVERSION", 72, ["Price extended but trend filters are not dominant"])


class StrategyEngine:
    """Select strategy and strikes based on detected market regime."""

    def recommend(self, market: MarketSnapshot, regime: RegimeResult) -> StrategyRecommendation:
        strikes = self.select_strikes(market, regime.regime)
        mapping = {
            "SIDEWAYS": "ATM Short Straddle",
            "TRENDING": "OTM1 Short Strangle",
            "VOLATILE": "Iron Condor",
            "EXPANSION": "Wide Iron Condor",
            "MEAN REVERSION": "ATM Short Straddle",
            "NO TRADE": "Skip Trade",
        }
        name = mapping.get(regime.regime, "Skip Trade")
        if market.iv_rank > 70 and regime.regime == "VOLATILE":
            name = "Wide Iron Condor"
        return StrategyRecommendation(name, strikes, regime.confidence, f"Selected for {regime.regime} regime")

    def select_strikes(self, market: MarketSnapshot, regime: str) -> StrikeSelection:
        """Calculate ATM, OTM1, OTM2, expected premium/theta/POP and recommendation."""
        strikes = sorted({q.strike for q in market.option_chain}) or [round(market.spot / 50) * 50]
        atm = min(strikes, key=lambda strike: abs(strike - market.spot))
        idx = strikes.index(atm)
        lower1 = strikes[max(0, idx - 1)]
        upper1 = strikes[min(len(strikes) - 1, idx + 1)]
        lower2 = strikes[max(0, idx - 2)]
        upper2 = strikes[min(len(strikes) - 1, idx + 2)]
        if regime == "TRENDING":
            call, put = upper1, lower1
        elif regime in {"VOLATILE", "EXPANSION"}:
            call, put = upper2, lower2
        else:
            call = put = atm
        expected_premium = self._premium(market.option_chain, call, "CE") + self._premium(market.option_chain, put, "PE")
        expected_theta = abs(self._theta(market.option_chain, call, "CE")) + abs(self._theta(market.option_chain, put, "PE"))
        pop = max(0.35, min(0.78, 0.68 - market.opening_range_pct / 10 - max(0, market.india_vix - 12) / 100))
        return StrikeSelection(atm, upper1, upper2, call, put, round(expected_premium, 2), round(expected_theta, 2), round(pop * 100, 1))

    def _premium(self, chain: list[OptionQuote], strike: int, option_type: str) -> float:
        return next((q.ltp for q in chain if q.strike == strike and q.option_type == option_type), 0.0)

    def _theta(self, chain: list[OptionQuote], strike: int, option_type: str) -> float:
        return next((q.theta for q in chain if q.strike == strike and q.option_type == option_type), 0.0)
